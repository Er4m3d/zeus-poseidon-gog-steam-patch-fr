# Construit le patch FR (dossier + ZIP) en comparant la version CD française et la version GOG.
param(
    [string]$SourceFR  = "C:\Sierra\Le Maître de l' Olympe  Zeus",
    [string]$SourceGOG = "C:\Program Files\GOG Galaxy\Games\Zeus and Poseidon",
    [string]$Sortie    = (Join-Path $PSScriptRoot 'dist'),
    [string]$SevenZip  = 'C:\Program Files\7-Zip\7z.exe',
    # Variante de secours : textes et noms de fichiers en ASCII, polices et Zeus.exe d'origine intacts.
    # Par défaut, les accents sont conservés et l'installateur corrige la table de caractères de Zeus.exe.
    [switch]$SansAccents
)
$ErrorActionPreference = 'Stop'
$Version = '1.5'
$Nom = if ($SansAccents) { "Patch_FR_Zeus_Poseidon_v${Version}_sans_accents" } else { "Patch_FR_Zeus_Poseidon_v$Version" }
. (Join-Path $PSScriptRoot 'tools\SansAccents.ps1')
. (Join-Path $PSScriptRoot 'tools\TableCaracteres.ps1')
$Dossier = Join-Path $Sortie $Nom
$Src = Join-Path $PSScriptRoot 'src'

# Seuls ces emplacements contiennent des données de langue ; le reste (exe, dll, config, doc, sauvegardes) est ignoré.
$Inclus  = '^(zeus_text\.eng|zeus_mm\.eng|zeus_editor_text\.eng|model\\.+|data\\.+|audio\\.+|binks\\.+|adventures\\.+)$'
$Exclus  = '(^|\\)vssver\.scc$'
# Fichiers anglais sans équivalent au même nom, à mettre de côté pour éviter les doublons dans la liste des campagnes.
$ARetirer = '^(adventures\\.+|audio\\voice\\campaign\\.+)$'

function Get-Index($racine) {
    $idx = @{}
    Get-ChildItem -LiteralPath $racine -Recurse -File | ForEach-Object {
        $rel = $_.FullName.Substring($racine.TrimEnd('\').Length + 1)
        $idx[$rel.ToLowerInvariant()] = [pscustomobject]@{ Rel = $rel; Chemin = $_.FullName; Taille = $_.Length }
    }
    $idx
}
function Get-Md5($f) { (Get-FileHash -LiteralPath $f -Algorithm MD5).Hash }

if (Test-Path -LiteralPath (Join-Path $SourceGOG 'Sauvegarde_VO_Patch_FR')) { throw "Le patch FR est installé dans $SourceGOG : désinstallez-le avant de reconstruire (la comparaison doit se faire avec la version anglaise d'origine)." }
Write-Host 'Indexation des deux installations...'
$fr = Get-Index $SourceFR
$gog = Get-Index $SourceGOG

if (Test-Path -LiteralPath $Dossier) { Remove-Item -LiteralPath $Dossier -Recurse -Force }
$DossierFichiers = Join-Path $Dossier 'fichiers'
New-Item -ItemType Directory -Path $DossierFichiers -Force | Out-Null

$copies = 0; $identiques = 0; $cibles = @{}
foreach ($k in $fr.Keys | Sort-Object) {
    if ($k -notmatch $Inclus -or $k -match $Exclus) { continue }
    # Sans accents, les polices anglaises d'origine suffisent (et sont celles que l'exe GOG affiche correctement)
    if ($SansAccents -and $k -match '^data\\zeus_fonts\.') { continue }
    $f = $fr[$k]; $g = $gog[$k]
    if ($g -and $g.Taille -eq $f.Taille -and (Get-Md5 $g.Chemin) -eq (Get-Md5 $f.Chemin)) { $identiques++; continue }
    $rel = if ($SansAccents) { ConvertTo-NomAscii $f.Rel } else { $f.Rel }
    if ($cibles.ContainsKey($rel.ToLowerInvariant())) { throw "Collision de noms après conversion ASCII : $rel" }
    $cibles[$rel.ToLowerInvariant()] = $true
    $dest = Join-Path $DossierFichiers $rel
    New-Item -ItemType Directory -Path (Split-Path -Parent $dest) -Force | Out-Null
    Copy-Item -LiteralPath $f.Chemin -Destination $dest
    (Get-Item -LiteralPath $dest).IsReadOnly = $false   # fichiers du CD souvent en lecture seule
    $copies++
}
Write-Host "  $copies fichiers FR à installer, $identiques identiques ignorés."

if ($SansAccents) {
    Write-Host 'Conversion des textes en ASCII...'
    foreach ($n in 'Zeus_Text.eng', 'Zeus_Editor_Text.eng') { $r = Convert-FichierTexteEng (Join-Path $DossierFichiers $n); Write-Host "  $n : $($r.Avant) -> $($r.Apres) octets" }
    $r = Convert-FichierMessagesEng (Join-Path $DossierFichiers 'Zeus_MM.eng'); Write-Host "  Zeus_MM.eng : $($r.Avant) -> $($r.Apres) octets"
    $bruts = @(Get-Item -LiteralPath (Join-Path $DossierFichiers 'Model\Zeus eventmsg.txt')) + @(Get-ChildItem -LiteralPath (Join-Path $DossierFichiers 'Adventures') -Recurse -Filter '*.txt')
    foreach ($b in $bruts) { $null = Convert-FichierTexteBrut $b.FullName }
    Write-Host "  $($bruts.Count) fichiers texte convertis."
    if ($script:Inconnus.Count) { Write-Host ('  Caractères sans équivalent remplacés par ? : ' + (($script:Inconnus.Keys | ForEach-Object { '0x{0:X2}' -f $_ }) -join ' ')) }
}

$retirer = $gog.Keys | Where-Object { $_ -match $ARetirer -and -not $fr.ContainsKey($_) } | Sort-Object | ForEach-Object { $gog[$_].Rel }
Write-Host "  $(@($retirer).Count) fichiers anglais à mettre de côté."

# Scripts et docs : UTF-8 avec BOM (PowerShell 5.1 / Bloc-notes) et fins de ligne CRLF (cmd.exe)
$utf8Bom = New-Object System.Text.UTF8Encoding($true)
function Write-Texte($source, $dest, $encodage) {
    $txt = [IO.File]::ReadAllText($source) -replace "`r?`n", "`r`n"
    New-Item -ItemType Directory -Path (Split-Path -Parent $dest) -Force | Out-Null
    [IO.File]::WriteAllText($dest, $txt, $encodage)
}
Write-Texte (Join-Path $Src 'scripts\patch.ps1') (Join-Path $Dossier 'scripts\patch.ps1') $utf8Bom
Write-Texte (Join-Path $Src 'LISEZMOI.txt') (Join-Path $Dossier 'LISEZMOI.txt') $utf8Bom
Write-Texte (Join-Path $Src 'INSTALLER.bat') (Join-Path $Dossier 'INSTALLER.bat') ([Text.Encoding]::ASCII)
Write-Texte (Join-Path $Src 'DESINSTALLER.bat') (Join-Path $Dossier 'DESINSTALLER.bat') ([Text.Encoding]::ASCII)
[IO.File]::WriteAllLines((Join-Path $Dossier 'scripts\fichiers_anglais_a_retirer.txt'), [string[]]$retirer, $utf8Bom)

if (-not $SansAccents) {
    # Les polices FR sont dessinées pour l'exe FR : l'installateur recopie dans l'exe GOG la table
    # caractère -> glyphe de l'exe FR et corrige le positionnement vertical des accents (tools\asm_accents.py).
    $exeGog = $gog['zeus.exe'].Chemin
    $tableGog = Get-TableCaracteres $exeGog
    $tableFr  = Get-TableCaracteres $fr['zeus.exe'].Chemin
    $offsetTable = Find-TableCaracteres ([IO.File]::ReadAllBytes($exeGog)) $exeGog
    $hex = { param($b) -join ($b | ForEach-Object { $_.ToString('X2') }) }
    $lignesCode = @(& python (Join-Path $PSScriptRoot 'tools\asm_accents.py') $exeGog)
    if ($LASTEXITCODE) { throw 'tools\asm_accents.py a échoué' }
    $nbDiff = @(0..($tableFr.Length - 1) | Where-Object { $tableFr[$_] -ne $tableGog[$_] }).Count
    Write-Host "  Zeus.exe : $nbDiff valeurs de table + $($lignesCode.Count) modifications de positionnement des accents."
    [IO.File]::WriteAllLines((Join-Path $Dossier 'scripts\zeus_exe_patch.txt'), [string[]](@(
        '# Correctif des accents pour Zeus.exe GOG/Steam 2.1.4.0 : offset octets_d''origine nouveaux_octets (hexadécimal)',
        ('{0:X} {1} {2}' -f $offsetTable, (& $hex $tableGog), (& $hex $tableFr))) + $lignesCode), $utf8Bom)
}

$zip = Join-Path $Sortie "$Nom.zip"
if (Test-Path -LiteralPath $zip) { Remove-Item -LiteralPath $zip -Force }
Write-Host 'Création du ZIP...'
Push-Location $Sortie
try { & $SevenZip a -tzip -mcu=on -mx=5 $zip $Nom | Out-Null; if ($LASTEXITCODE) { throw "7-Zip a échoué ($LASTEXITCODE)" } }
finally { Pop-Location }
'{0}  ({1:N0} Mo)' -f $zip, ((Get-Item -LiteralPath $zip).Length / 1MB)
