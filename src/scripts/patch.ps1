#Requires -Version 5.1
<#
    Patch de traduction française - Le Maître de l'Olympe : Zeus & Poséidon (versions GOG et Steam)

    Installation   : powershell -ExecutionPolicy Bypass -File patch.ps1
    Désinstallation: powershell -ExecutionPolicy Bypass -File patch.ps1 -Desinstaller
    Options        : -DossierJeu "<chemin>"  force le dossier du jeu
                     -Plateforme GOG|Steam   choisit la version détectée à patcher
                     -SansAnimations         n'applique pas le correctif d'animations (ZIP de Pecunia)
                     -Resolution 1920x1080   variante du mod grand écran à installer (« aucune » : 1024x768)
                     -Oui                    ne pose aucune question (mode silencieux)
#>
param(
    [string]$DossierJeu,
    [ValidateSet('GOG', 'Steam')]
    [string]$Plateforme,
    [switch]$SansAnimations,
    [string]$Resolution,
    [switch]$Desinstaller,
    [switch]$Oui
)

$ErrorActionPreference = 'Stop'
$VersionPatch   = '1.6'
$RacinePatch    = Split-Path -Parent $PSScriptRoot
$DossierFichiers = Join-Path $RacinePatch 'fichiers'
$ListeARetirer  = Join-Path $PSScriptRoot 'fichiers_anglais_a_retirer.txt'
$NomSauvegarde  = 'Sauvegarde_VO_Patch_FR'
$GogId          = '1207659039'
$SteamId        = '566050'

function Titre($texte) {
    Write-Host ''
    Write-Host ('=' * 70) -ForegroundColor DarkYellow
    Write-Host "  $texte" -ForegroundColor Yellow
    Write-Host ('=' * 70) -ForegroundColor DarkYellow
    Write-Host ''
}

function Fin($code) {
    # dossier temporaire d'extraction du mod grand écran
    if ($script:DossierTempHD -and (Test-Path -LiteralPath $script:DossierTempHD)) {
        try {
            Get-ChildItem -LiteralPath $script:DossierTempHD -Recurse -File | ForEach-Object { $_.IsReadOnly = $false }   # fichiers de l'archive en lecture seule
            [IO.Directory]::Delete($script:DossierTempHD, $true)
        } catch { Write-Host "Impossible de supprimer le dossier temporaire $($script:DossierTempHD)" -ForegroundColor Yellow }
    }
    if (-not $Oui) {
        Write-Host ''
        Read-Host 'Appuyez sur Entrée pour fermer cette fenêtre' | Out-Null
    }
    exit $code
}

function Erreur($message) {
    Write-Host ''
    Write-Host "ERREUR : $message" -ForegroundColor Red
    Fin 1
}

function Confirmer($question) {
    if ($Oui) { return $true }
    $r = Read-Host "$question (O/N)"
    return $r -match '^\s*[oOyY]'
}

function Test-DossierJeu($d) {
    if (-not $d) { return $false }
    return (Test-Path -LiteralPath (Join-Path $d 'Zeus.exe')) -and
           (Test-Path -LiteralPath (Join-Path $d 'Zeus_Text.eng')) -and
           (Test-Path -LiteralPath (Join-Path $d 'Adventures'))
}

function Get-PlateformeDossier($d) {
    if ($d -match '\\steamapps\\') { return 'Steam' }
    return 'GOG'
}

function Get-DossiersGog {
    $c = @()
    foreach ($cle in "HKLM:\SOFTWARE\WOW6432Node\GOG.com\Games\$GogId", "HKLM:\SOFTWARE\GOG.com\Games\$GogId") {
        try { $c += (Get-ItemProperty -LiteralPath $cle -ErrorAction Stop).path } catch {}
    }
    foreach ($cle in "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\${GogId}_is1",
                     "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\${GogId}_is1") {
        try { $c += (Get-ItemProperty -LiteralPath $cle -ErrorAction Stop).InstallLocation } catch {}
    }
    $c += @(
        (Join-Path $env:ProgramFiles 'GOG Galaxy\Games\Zeus and Poseidon'),
        (Join-Path ${env:ProgramFiles(x86)} 'GOG Galaxy\Games\Zeus and Poseidon'),
        'C:\GOG Games\Zeus and Poseidon'
    )
    return $c
}

function Get-DossiersSteam {
    # Dossier Steam principal, puis bibliothèques secondaires listées dans libraryfolders.vdf
    $racines = @()
    foreach ($cle in 'HKLM:\SOFTWARE\WOW6432Node\Valve\Steam', 'HKLM:\SOFTWARE\Valve\Steam') {
        try { $racines += (Get-ItemProperty -LiteralPath $cle -ErrorAction Stop).InstallPath } catch {}
    }
    try { $racines += ((Get-ItemProperty -LiteralPath 'HKCU:\SOFTWARE\Valve\Steam' -ErrorAction Stop).SteamPath -replace '/', '\') } catch {}
    $racines += (Join-Path ${env:ProgramFiles(x86)} 'Steam')
    $biblios = @()
    foreach ($r in $racines | Where-Object { $_ } | Select-Object -Unique) {
        $biblios += $r
        $vdf = Join-Path $r 'steamapps\libraryfolders.vdf'
        if (Test-Path -LiteralPath $vdf) {
            foreach ($m in [regex]::Matches([IO.File]::ReadAllText($vdf), '"path"\s+"([^"]+)"')) { $biblios += ($m.Groups[1].Value -replace '\\\\', '\') }
        }
    }
    $c = @()
    foreach ($b in $biblios | Select-Object -Unique) {
        $nom = 'Zeus + Poseidon'
        $acf = Join-Path $b "steamapps\appmanifest_$SteamId.acf"
        if (Test-Path -LiteralPath $acf) {
            $m = [regex]::Match([IO.File]::ReadAllText($acf), '"installdir"\s+"([^"]+)"')
            if ($m.Success) { $nom = $m.Groups[1].Value }
        }
        $c += (Join-Path $b "steamapps\common\$nom")
    }
    return $c
}

# Retourne les installations trouvées : @{ Plateforme; Dossier; Patche }
function Find-InstallationsJeu {
    $vus = @{}
    $res = @()
    $candidats = @(Get-DossiersGog | ForEach-Object { @{ P = 'GOG'; D = $_ } }) +
                 @(Get-DossiersSteam | ForEach-Object { @{ P = 'Steam'; D = $_ } }) +
                 @(@{ P = $null; D = (Split-Path -Parent $RacinePatch) })   # patch extrait dans le dossier du jeu
    foreach ($c in $candidats) {
        if (-not $c.D -or -not (Test-DossierJeu $c.D)) { continue }
        $d = (Resolve-Path -LiteralPath $c.D).Path.TrimEnd('\')
        if ($vus.ContainsKey($d.ToLowerInvariant())) { continue }
        $vus[$d.ToLowerInvariant()] = $true
        $p = if ($c.P) { $c.P } else { Get-PlateformeDossier $d }
        $res += [pscustomobject]@{ Plateforme = $p; Dossier = $d; Patche = (Test-Path -LiteralPath (Join-Path $d "$NomSauvegarde\manifeste.txt")) }
    }
    return $res
}

function Select-DossierJeu {
    Add-Type -AssemblyName System.Windows.Forms
    $dlg = New-Object System.Windows.Forms.FolderBrowserDialog
    $dlg.Description = "Sélectionnez le dossier d'installation de « Zeus and Poseidon » / « Zeus + Poseidon » (celui qui contient Zeus.exe)"
    $dlg.ShowNewFolderButton = $false
    if ($dlg.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { return $dlg.SelectedPath }
    return $null
}

function Test-Admin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    return ([Security.Principal.WindowsPrincipal]$id).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-Ecriture($d) {
    $test = Join-Path $d ('.patchfr_test_' + [guid]::NewGuid().ToString('N'))
    try { [IO.File]::WriteAllText($test, 'x'); Remove-Item -LiteralPath $test -Force; return $true } catch { return $false }
}

function Remove-DossiersVides($racine, $sousDossier) {
    $base = Join-Path $racine $sousDossier
    if (-not (Test-Path -LiteralPath $base)) { return }
    Get-ChildItem -LiteralPath $base -Recurse -Directory |
        Sort-Object { $_.FullName.Length } -Descending |
        Where-Object { -not (Get-ChildItem -LiteralPath $_.FullName -Force) } |
        ForEach-Object { Remove-Item -LiteralPath $_.FullName -Force }
}

function Copy-Fichier($source, $dest) {
    $parent = Split-Path -Parent $dest
    if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    Copy-Item -LiteralPath $source -Destination $dest -Force
}

function Move-Fichier($source, $dest) {
    $parent = Split-Path -Parent $dest
    if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    Move-Item -LiteralPath $source -Destination $dest -Force
}

# ---------------------------------------------------------------------------
$action = if ($Desinstaller) { 'Désinstallation' } else { 'Installation' }
Titre "Patch FR v$VersionPatch - Le Maître de l'Olympe : Zeus & Poséidon (GOG / Steam) - $action"

if (-not $Desinstaller -and -not (Test-Path -LiteralPath (Join-Path $DossierFichiers 'Zeus_Text.eng'))) {
    Erreur "Le dossier « fichiers » du patch est introuvable. Avez-vous bien extrait tout le ZIP avant de lancer l'installation ?"
}

# 1. Dossier du jeu
if ($DossierJeu) {
    $DossierJeu = $DossierJeu.Trim('"').TrimEnd('\')
    if (-not (Test-DossierJeu $DossierJeu)) { Erreur "Le dossier « $DossierJeu » ne contient pas Zeus and Poseidon." }
} else {
    $installations = @(Find-InstallationsJeu)
    if ($Desinstaller -and @($installations | Where-Object Patche).Count -gt 0) {
        $installations = @($installations | Where-Object Patche)   # ne proposer que les versions patchées
    }
    if ($Plateforme) {
        $installations = @($installations | Where-Object Plateforme -eq $Plateforme)
        if ($installations.Count -eq 0) { Erreur "Aucune version $Plateforme du jeu n'a été trouvée. Utilisez -DossierJeu `"<chemin>`"." }
    }

    if ($installations.Count -eq 0) {
        Write-Host "Le jeu n'a pas été trouvé automatiquement." -ForegroundColor Yellow
    } elseif ($installations.Count -eq 1 -and ($Oui -or $Plateforme)) {
        $DossierJeu = $installations[0].Dossier
        Write-Host "Version $($installations[0].Plateforme) : $DossierJeu" -ForegroundColor Green
    } elseif ($Oui) {
        Erreur 'Plusieurs versions du jeu sont installées : précisez -Plateforme GOG|Steam ou -DossierJeu "<chemin>".'
    } else {
        Write-Host 'Versions du jeu détectées :'
        Write-Host ''
        for ($i = 0; $i -lt $installations.Count; $i++) {
            $etat = if ($installations[$i].Patche) { '  (patch FR installé)' } else { '' }
            Write-Host ("  [{0}] {1,-6} {2}{3}" -f ($i + 1), $installations[$i].Plateforme, $installations[$i].Dossier, $etat)
        }
        Write-Host  '  [A]    Autre dossier...'
        Write-Host ''
        while ($true) {
            $r = "$(Read-Host "Quelle version voulez-vous $(if ($Desinstaller) { 'restaurer en anglais' } else { 'patcher' }) ? (1-$($installations.Count) ou A)")".Trim()
            if ($r -match '^\d+$' -and [int]$r -ge 1 -and [int]$r -le $installations.Count) { $DossierJeu = $installations[[int]$r - 1].Dossier; break }
            if ($r -match '^[aA]$') { break }
            if ($r -eq '') { Erreur 'Aucun choix. Opération annulée.' }
            Write-Host 'Choix invalide.' -ForegroundColor Yellow
        }
    }
    while (-not $DossierJeu) {
        if ($Oui) { Erreur 'Dossier du jeu introuvable. Utilisez -DossierJeu "<chemin>".' }
        Write-Host 'Veuillez sélectionner le dossier du jeu dans la fenêtre qui vient de s''ouvrir...'
        $choix = Select-DossierJeu
        if (-not $choix) { Erreur 'Aucun dossier sélectionné. Opération annulée.' }
        if (Test-DossierJeu $choix) { $DossierJeu = $choix.TrimEnd('\') }
        else { Write-Host "« $choix » ne contient pas Zeus.exe / Zeus_Text.eng / Adventures. Réessayez." -ForegroundColor Yellow }
    }
}

# 2. Droits administrateur si nécessaire (ex. C:\Program Files)
if (-not (Test-Ecriture $DossierJeu)) {
    if (Test-Admin) { Erreur "Impossible d'écrire dans « $DossierJeu »." }
    Write-Host 'Des droits administrateur sont nécessaires pour modifier ce dossier. Une fenêtre de confirmation Windows va s''ouvrir...' -ForegroundColor Yellow
    $arguments = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$PSCommandPath`"", '-DossierJeu', "`"$DossierJeu`"")
    if ($Desinstaller) { $arguments += '-Desinstaller' }
    if ($Oui) { $arguments += '-Oui' }
    if ($SansAnimations) { $arguments += '-SansAnimations' }
    if ($Resolution) { $arguments += @('-Resolution', "`"$Resolution`"") }
    try {
        $p = Start-Process -FilePath 'powershell.exe' -ArgumentList $arguments -Verb RunAs -PassThru -Wait
        exit $p.ExitCode
    } catch {
        Erreur 'Les droits administrateur ont été refusés. Opération annulée.'
    }
}

# 3. Le jeu ne doit pas tourner
if (Get-Process -Name 'Zeus' -ErrorAction SilentlyContinue) {
    Erreur 'Zeus est en cours d''exécution. Fermez le jeu puis relancez le patch.'
}

$DossierSauvegarde = Join-Path $DossierJeu $NomSauvegarde
$Manifeste = Join-Path $DossierSauvegarde 'manifeste.txt'

# Manifeste : une ligne par fichier -> "N|chemin" (ajouté), "R|chemin" (remplacé, original sauvegardé), "M|chemin" (fichier anglais mis de côté)
function Read-Manifeste {
    $m = [ordered]@{}
    if (Test-Path -LiteralPath $Manifeste) {
        foreach ($l in [IO.File]::ReadAllLines($Manifeste, [Text.Encoding]::UTF8)) {
            if ($l -match '^([NRM])\|(.+)$') { $m[$Matches[2].ToLowerInvariant()] = @{ Type = $Matches[1]; Chemin = $Matches[2] } }
        }
    }
    return $m
}
function Add-Manifeste($type, $chemin) {
    [IO.File]::AppendAllText($Manifeste, "$type|$chemin`r`n", [Text.Encoding]::UTF8)
}

# ---------------------------------------------------------------------------
if ($Desinstaller) {
    if (-not (Test-Path -LiteralPath $Manifeste)) { Erreur "Le patch FR ne semble pas installé dans « $DossierJeu » (aucune sauvegarde trouvée)." }
    if (-not (Confirmer 'Restaurer la version anglaise d''origine ?')) { Write-Host 'Annulé.'; Fin 0 }

    $entrees = @((Read-Manifeste).Values)
    $i = 0; $erreurs = 0
    foreach ($e in $entrees) {
        $i++
        Write-Progress -Activity 'Restauration de la version anglaise' -Status $e.Chemin -PercentComplete ($i * 100 / [Math]::Max(1, $entrees.Count))
        $cible = Join-Path $DossierJeu $e.Chemin
        $sauve = Join-Path $DossierSauvegarde $e.Chemin
        try {
            if ($e.Type -eq 'N') {
                if (Test-Path -LiteralPath $cible) { Remove-Item -LiteralPath $cible -Force }
            } elseif (Test-Path -LiteralPath $sauve) {
                Move-Fichier $sauve $cible
            }
        } catch { $erreurs++; Write-Host "  Impossible de restaurer : $($e.Chemin) ($($_.Exception.Message))" -ForegroundColor Red }
    }
    Write-Progress -Activity 'Restauration de la version anglaise' -Completed
    Remove-DossiersVides $DossierJeu 'Adventures'
    Remove-DossiersVides $DossierJeu 'Audio'

    if ($erreurs -eq 0) {
        Remove-Item -LiteralPath $DossierSauvegarde -Recurse -Force
        Write-Host 'Désinstallation terminée : le jeu est revenu en anglais.' -ForegroundColor Green
    } else {
        Write-Host "$erreurs fichier(s) n'ont pas pu être restaurés. La sauvegarde est conservée dans : $DossierSauvegarde" -ForegroundColor Yellow
    }
    Fin ([int]($erreurs -gt 0))
}

# ---------------------------------------------------------------------------
# Installation
$exe = Get-Item -LiteralPath (Join-Path $DossierJeu 'Zeus.exe')
if ($exe.VersionInfo.FileVersion -notlike '2.1*') {
    Write-Host "Attention : Zeus.exe est en version « $($exe.VersionInfo.FileVersion) » ; ce patch a été préparé pour la version 2.1 (GOG)." -ForegroundColor Yellow
    if (-not (Confirmer 'Continuer quand même ?')) { Write-Host 'Annulé.'; Fin 0 }
}

# Correctif des accents dans Zeus.exe : les polices FR ne s'affichent correctement qu'avec la table
# caractère -> glyphe et le positionnement vertical des accents de l'exe FR. Chaque ligne du fichier
# donne « offset octets_d'origine nouveaux_octets » ; chaque zone doit être soit d'origine, soit déjà corrigée.
#
# Correctif d'animations (facultatif) : « Zeus/Poseidon Animation Fix Patch » de Pecunia (2018), non inclus.
# Si son ZIP est posé à côté d'INSTALLER.bat, son Zeus.exe sert de base avant le correctif des accents
# (les deux correctifs ne touchent pas les mêmes octets).
$Md5ExeOrigine   = '7423A12681188325CAB04F72B7DC64F1'   # Zeus.exe GOG / Steam 2.1.4.0
$Md5ExeAnimation = 'EDD8DB10D804AD41D501871644192D08'   # Zeus.exe du correctif d'animations
# Mod grand écran « ZEUS_WIDE1 » (non inclus) : Zeus.exe de chaque résolution, basés sur l'exe GOG / Steam
$Md5ExeHD = @{
    '1280x1024' = '84854C140AD21821F709CDF49375F0EC'; '1280x720' = '0284F5A2C7DE31B163E67E46CA5D632F'
    '1280x800' = '46AE3EE28846C9A0CAD6B1CFB418D3BE'; '1360x768\Version 1' = '8B03C4EE091C5D92578C35C1D4A358B1'
    '1360x768\Version 2' = '292874FE7C8054E1EE64B7722F69D51B'; '1440x900' = '3F07D106A9BE6BC48E016CE6AB22FFDA'
    '1600x900' = 'AD4E873BC7FA5CED1169E5D9424BE2CE'; '1680x1050' = '24F112D083CDFDF4255490A5CF89738E'
    '1920x1080' = 'BFAC58814D0991ED676F52B9612BFD5E'; '1920x1200' = '8A895906B5B2EA865DB9C3A3E7A5EACB'
    '2048x1152' = 'BFFDD4C4B3B59083580414C8C80FADA3'; '2560x1440' = '75A6F258B4F5D3265109754F699AAEE8'
    '2560x1600' = '6C6B41E60831CCCADF4383D87782EF1F'
}
$FichierPatchExe = Join-Path $PSScriptRoot 'zeus_exe_patch.txt'
$PatchExe = @()
if (Test-Path -LiteralPath $FichierPatchExe) {
    $versOctets = { param($h) [byte[]]@(for ($j = 0; $j -lt $h.Length; $j += 2) { [Convert]::ToByte($h.Substring($j, 2), 16) }) }
    foreach ($l in [IO.File]::ReadAllLines($FichierPatchExe)) {
        if ($l -match '^([0-9A-F]+) ([0-9A-F]+) ([0-9A-F]+)$') {
            $PatchExe += [pscustomobject]@{ Offset = [Convert]::ToInt64($Matches[1], 16); Origine = (& $versOctets $Matches[2]); Nouveau = (& $versOctets $Matches[3]) }
        }
    }
}
function Test-Octets([byte[]]$b, [long]$off, [byte[]]$attendu) {
    if ($off + $attendu.Length -gt $b.Length) { return $false }
    for ($j = 0; $j -lt $attendu.Length; $j++) { if ($b[$off + $j] -ne $attendu[$j]) { return $false } }
    return $true
}
function Get-Md5([byte[]]$b) {
    $h = [Security.Cryptography.MD5]::Create()
    try { return ([BitConverter]::ToString($h.ComputeHash($b)) -replace '-', '') } finally { $h.Dispose() }
}

function Read-EntreeZip([string]$zip, [string]$nom) {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = [IO.Compression.ZipFile]::OpenRead($zip)
    try {
        $entree = $archive.Entries | Where-Object { $_.Name -ieq $nom } | Select-Object -First 1
        if (-not $entree) { return $null }
        $ms = New-Object IO.MemoryStream
        $flux = $entree.Open(); try { $flux.CopyTo($ms) } finally { $flux.Dispose() }
        return , $ms.ToArray()
    } finally { $archive.Dispose() }
}
function Find-SevenZip {
    foreach ($c in (Join-Path $env:ProgramFiles '7-Zip\7z.exe'), (Join-Path ${env:ProgramFiles(x86)} '7-Zip\7z.exe')) { if (Test-Path -LiteralPath $c) { return $c } }
    $c = Get-Command 7z.exe -ErrorAction SilentlyContinue
    if ($c) { return $c.Source }
    return $null
}
function Get-ResolutionEcran {
    try {
        $v = Get-CimInstance Win32_VideoController -ErrorAction Stop | Where-Object CurrentHorizontalResolution | Sort-Object CurrentHorizontalResolution -Descending | Select-Object -First 1
        if ($v) { return "$($v.CurrentHorizontalResolution)x$($v.CurrentVerticalResolution)" }
    } catch {}
    return $null
}

# 1) Exe du jeu ramené à son état sans le correctif des accents
$octetsExe = [IO.File]::ReadAllBytes($exe.FullName)
$exeBase = [byte[]]$octetsExe.Clone()
foreach ($p in $PatchExe) {
    if (Test-Octets $octetsExe $p.Offset $p.Nouveau) { [Array]::Copy($p.Origine, 0, $exeBase, $p.Offset, $p.Origine.Length); continue }
    if (Test-Octets $octetsExe $p.Offset $p.Origine) { continue }
    Erreur 'Ce Zeus.exe n''est pas reconnu : ce patch est prévu pour la version 2.1.4.0 (GOG ou Steam). Aucune modification n''a été faite.'
}
$md5Base = Get-Md5 $exeBase

# Exe GOG / Steam d'origine : l'exe actuel, ou celui sauvegardé lors d'une installation précédente
$exeOrigine = $null
if ($md5Base -eq $Md5ExeOrigine) { $exeOrigine = $exeBase }
else {
    $sauveExe = Join-Path $DossierSauvegarde 'Zeus.exe'
    if (Test-Path -LiteralPath $sauveExe) {
        $b = [IO.File]::ReadAllBytes($sauveExe)
        if ((Get-Md5 $b) -eq $Md5ExeOrigine) { $exeOrigine = $b }
    }
}

# 2) Correctifs facultatifs posés à côté d'INSTALLER.bat
$exeAnimation = $null
$zipAnimation = Get-ChildItem -LiteralPath $RacinePatch -Filter '*animation*patch*.zip' -File -ErrorAction SilentlyContinue | Select-Object -First 1
if ($zipAnimation -and -not $SansAnimations) {
    $b = Read-EntreeZip $zipAnimation.FullName 'Zeus.exe'
    if ($b -and (Get-Md5 $b) -eq $Md5ExeAnimation) { $exeAnimation = $b }
    else { Write-Host "Ignoré : $($zipAnimation.Name) ne contient pas le Zeus.exe attendu du correctif d'animations (version d'avril 2018)." -ForegroundColor Yellow }
}

# Mod grand écran (« ZEUS_WIDE1 ») : dossier extrait ou archive .7z
$VariantesHD = @()
$dossierHD = Get-ChildItem -LiteralPath $RacinePatch -Directory -Recurse -Depth 2 -Filter 'ZEUS_WIDE1' -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $dossierHD -and $Resolution -ne 'aucune') {
    foreach ($a7z in Get-ChildItem -LiteralPath $RacinePatch -Filter '*.7z' -File -ErrorAction SilentlyContinue) {
        $sz = Find-SevenZip
        if (-not $sz) { Write-Host "Mod grand écran : pour utiliser $($a7z.Name), installez 7-Zip ou extrayez l'archive à côté d'INSTALLER.bat." -ForegroundColor Yellow; break }
        if (-not ((& $sz l -ba $a7z.FullName) -match 'ZEUS_WIDE1')) { continue }
        $script:DossierTempHD = Join-Path ([IO.Path]::GetTempPath()) ('PatchFR_ZeusHD_' + [guid]::NewGuid().ToString('N'))
        Write-Host "Mod grand écran : extraction de $($a7z.Name)..."
        & $sz x $a7z.FullName "-o$script:DossierTempHD" -y | Out-Null
        $dossierHD = Get-ChildItem -LiteralPath $script:DossierTempHD -Directory -Recurse -Filter 'ZEUS_WIDE1' | Select-Object -First 1
        break
    }
}
if ($dossierHD) {
    foreach ($e in Get-ChildItem -LiteralPath $dossierHD.FullName -Recurse -Filter 'Zeus.exe' -File) {
        $nom = $e.DirectoryName.Substring($dossierHD.FullName.Length + 1)
        if ($Md5ExeHD[$nom] -and (Get-FileHash -LiteralPath $e.FullName -Algorithm MD5).Hash -eq $Md5ExeHD[$nom] -and (Test-Path -LiteralPath (Join-Path $e.DirectoryName 'DATA'))) {
            $VariantesHD += [pscustomobject]@{ Nom = $nom; Dossier = $e.DirectoryName }
        }
    }
    $VariantesHD = @($VariantesHD | Sort-Object { [int]($_.Nom -replace 'x.*', '') }, Nom)
    if ($VariantesHD.Count -eq 0) { Write-Host 'Mod grand écran : aucune variante reconnue dans ZEUS_WIDE1.' -ForegroundColor Yellow }
}

$VarianteHD = $null
$ExeReconstruit = $false
$AnimationAppliquee = $false
if ($Resolution -and $Resolution -ne 'aucune' -and -not $VariantesHD.Count) {
    Write-Host "Option -Resolution ignorée : le mod grand écran (ZEUS_WIDE1 ou .7z) n'est pas à côté d'INSTALLER.bat." -ForegroundColor Yellow
}
$ExeGere = $PatchExe.Count -gt 0
if (($exeAnimation -or $VariantesHD.Count) -and -not $exeOrigine) {
    Write-Host 'Correctifs facultatifs ignorés : l''exe GOG / Steam d''origine est introuvable (ni dans le jeu, ni dans la sauvegarde).' -ForegroundColor Yellow
} elseif ($exeAnimation -or $VariantesHD.Count) {
    # Choix de la résolution
    if ($VariantesHD.Count) {
        $ecran = Get-ResolutionEcran
        $defaut = 0
        for ($i = 0; $i -lt $VariantesHD.Count; $i++) { if (-not $defaut -and ($VariantesHD[$i].Nom -split '\\')[0] -eq $ecran) { $defaut = $i + 1 } }
        if ($Resolution) {
            $defaut = 0
            for ($i = 0; $i -lt $VariantesHD.Count; $i++) { if ($VariantesHD[$i].Nom -ieq $Resolution -or ($VariantesHD[$i].Nom -split '\\')[0] -ieq $Resolution) { $defaut = $i + 1; break } }
            if (-not $defaut -and $Resolution -ne 'aucune') { Erreur "Résolution « $Resolution » absente du mod grand écran." }
            $choix = $defaut
        } elseif ($Oui) {
            $choix = $defaut
        } else {
            Write-Host ''
            Write-Host "Mod grand écran trouvé (écran détecté : $(if ($ecran) { $ecran } else { 'inconnu' })) :"
            Write-Host '  [0]  Aucune : résolution d''origine (1024x768)'
            for ($i = 0; $i -lt $VariantesHD.Count; $i++) { Write-Host ("  [{0}] {1}{2}" -f ($i + 1), $VariantesHD[$i].Nom, $(if ($i + 1 -eq $defaut) { '   <- votre écran' })) }
            while ($true) {
                $r = "$(Read-Host "Résolution à installer (Entrée = $defaut)")".Trim()
                if ($r -eq '') { $choix = $defaut; break }
                if ($r -match '^\d+$' -and [int]$r -le $VariantesHD.Count) { $choix = [int]$r; break }
                Write-Host 'Choix invalide.' -ForegroundColor Yellow
            }
        }
        if ($choix -gt 0) { $VarianteHD = $VariantesHD[$choix - 1] }
    }
    if ($exeAnimation) {
        Write-Host ''
        Write-Host "Correctif d'animations trouvé : $($zipAnimation.Name)" -ForegroundColor Green
        Write-Host '  (dieux trop lents, ramasseurs d''oursins, autres animations - patch de Pecunia)'
        $AnimationAppliquee = Confirmer 'Appliquer aussi le correctif d''animations ?'
    }
    # Exe reconstruit à partir de l'original : grand écran, puis animations
    $exeBase = if ($VarianteHD) { [IO.File]::ReadAllBytes((Join-Path $VarianteHD.Dossier 'Zeus.exe')) } else { [byte[]]$exeOrigine.Clone() }
    if ($AnimationAppliquee) {
        for ($i = 0; $i -lt $exeOrigine.Length; $i++) {
            if ($exeAnimation[$i] -ne $exeOrigine[$i]) {
                if ($exeBase[$i] -ne $exeOrigine[$i]) { Erreur 'Le correctif d''animations et le mod grand écran modifient les mêmes octets : combinaison impossible.' }
                $exeBase[$i] = $exeAnimation[$i]
            }
        }
    }
    $ExeGere = $true
    $ExeReconstruit = $true
    if ($VarianteHD) { Write-Host "Mod grand écran : $($VarianteHD.Nom)" -ForegroundColor Green }
} elseif ($md5Base -eq $Md5ExeAnimation) {
    $AnimationAppliquee = $true   # exe d'animations posé à la main, sans sauvegarde de l'original : conservé
    $ExeGere = $true
}
Write-Host ''

# 3) Exe final = base + correctif des accents
$ExeCible = [byte[]]$exeBase.Clone()
foreach ($p in $PatchExe) { [Array]::Copy($p.Nouveau, 0, $ExeCible, $p.Offset, $p.Nouveau.Length) }
$ExeAModifier = (Get-Md5 $ExeCible) -ne (Get-Md5 $octetsExe)
$TableFr = $ExeGere   # Zeus.exe fait partie de ce qui est installé

$manifesteActuel = Read-Manifeste
if ($manifesteActuel.Count -gt 0) {
    Write-Host 'Le patch FR est déjà installé : les fichiers français vont être réinstallés (la sauvegarde anglaise existante est conservée).' -ForegroundColor Yellow
}

# Fichiers à installer : traduction, puis images du mod grand écran (résolution choisie)
$prefixe = $DossierFichiers.TrimEnd('\').Length + 1
$fichiers = @(Get-ChildItem -LiteralPath $DossierFichiers -Recurse -File | ForEach-Object {
    [pscustomobject]@{ Source = $_.FullName; Rel = $_.FullName.Substring($prefixe); Length = $_.Length } })
$nbTraduction = $fichiers.Count
if ($VarianteHD) {
    $fichiers += @(Get-ChildItem -LiteralPath (Join-Path $VarianteHD.Dossier 'DATA') -File | ForEach-Object {
        [pscustomobject]@{ Source = $_.FullName; Rel = "DATA\$($_.Name)"; Length = $_.Length } })
}
# Sans fichiers du mod grand écran à côté d'INSTALLER.bat, un mod déjà installé (exe conservé) garde ses images
$GarderImagesHD = -not $ExeReconstruit -and $exeOrigine -and $md5Base -notin @($Md5ExeOrigine, $Md5ExeAnimation)
if ($GarderImagesHD) { $TableFr = $true }   # l'exe grand écran en place fait partie de l'installation
$aRetirer = @()
if (Test-Path -LiteralPath $ListeARetirer) {
    $aRetirer = @([IO.File]::ReadAllLines($ListeARetirer, [Text.Encoding]::UTF8) | Where-Object { $_.Trim() })
}
$tailleMo = [Math]::Round((($fichiers | Measure-Object Length -Sum).Sum) / 1MB)
Write-Host "Le patch va installer $nbTraduction fichiers français$(if ($VarianteHD) { " et $($fichiers.Count - $nbTraduction) images grand écran" }) ($tailleMo Mo)."
Write-Host "Les fichiers anglais remplacés seront sauvegardés dans : $DossierSauvegarde"
Write-Host ''
if (-not (Confirmer 'Lancer l''installation ?')) { Write-Host 'Annulé.'; Fin 0 }

$libre = (Get-PSDrive -Name ($DossierJeu.Substring(0, 1))).Free
if ($libre -and $libre -lt 2 * ($tailleMo * 1MB)) { Erreur "Espace disque insuffisant (il faut environ $(2 * $tailleMo) Mo libres)." }

New-Item -ItemType Directory -Path $DossierSauvegarde -Force | Out-Null

try {
    # Mise à jour depuis une version précédente du patch : suppression des fichiers ajoutés
    # qui n'existent plus sous ce nom (ex. noms accentués de la v1.0)
    if ($manifesteActuel.Count -gt 0) {
        $nouveaux = @{}
        foreach ($f in $fichiers) { $nouveaux[$f.Rel.ToLowerInvariant()] = $true }
        if ($TableFr) { $nouveaux['zeus.exe'] = $true }
        $obsoletes = @($manifesteActuel.Keys | Where-Object {
            $manifesteActuel[$_].Type -in 'N', 'R' -and -not $nouveaux.ContainsKey($_) -and -not ($GarderImagesHD -and $_ -match '^data\\[^\\]+\.jpg$') })
        if ($obsoletes.Count) {
            Write-Host "Nettoyage de $($obsoletes.Count) fichiers d'une version précédente du patch..."
            foreach ($k in $obsoletes) {
                $e = $manifesteActuel[$k]
                $cible = Join-Path $DossierJeu $e.Chemin
                if ($e.Type -eq 'N') {
                    if (Test-Path -LiteralPath $cible) { Remove-Item -LiteralPath $cible -Force }
                } else {
                    # fichier d'origine que ce patch ne remplace plus : on remet l'original
                    $sauve = Join-Path $DossierSauvegarde $e.Chemin
                    if (Test-Path -LiteralPath $sauve) { Move-Fichier $sauve $cible }
                }
                $manifesteActuel.Remove($k)
            }
            $lignes = foreach ($v in $manifesteActuel.Values) { "$($v.Type)|$($v.Chemin)" }
            [IO.File]::WriteAllLines($Manifeste, [string[]]$lignes, [Text.Encoding]::UTF8)
            Remove-DossiersVides $DossierJeu 'Adventures'
        }
    }

    # a) Mise de côté des aventures/campagnes anglaises (elles apparaîtraient en double dans la liste)
    foreach ($rel in $aRetirer) {
        $cible = Join-Path $DossierJeu $rel
        if (-not (Test-Path -LiteralPath $cible)) { continue }
        if ($manifesteActuel.Contains($rel.ToLowerInvariant())) {
            # déjà sauvegardé lors d'une installation précédente (fichier remis par GOG Galaxy ou Steam)
            Remove-Item -LiteralPath $cible -Force
        } else {
            Move-Fichier $cible (Join-Path $DossierSauvegarde $rel)
            Add-Manifeste 'M' $rel
        }
    }
    Remove-DossiersVides $DossierJeu 'Adventures'

    # b) Copie des fichiers français (avec sauvegarde des originaux)
    $i = 0
    foreach ($f in $fichiers) {
        $i++
        $rel = $f.Rel
        if ($i % 20 -eq 0 -or $i -eq $fichiers.Count) {
            Write-Progress -Activity 'Installation des fichiers français' -Status "$i / $($fichiers.Count) - $rel" -PercentComplete ($i * 100 / $fichiers.Count)
        }
        $cible = Join-Path $DossierJeu $rel
        if (-not $manifesteActuel.Contains($rel.ToLowerInvariant())) {
            if (Test-Path -LiteralPath $cible) {
                Copy-Fichier $cible (Join-Path $DossierSauvegarde $rel)
                Add-Manifeste 'R' $rel
            } else {
                Add-Manifeste 'N' $rel
            }
            $manifesteActuel[$rel.ToLowerInvariant()] = $true
        }
        Copy-Fichier $f.Source $cible
    }
    Write-Progress -Activity 'Installation des fichiers français' -Completed

    # c) Zeus.exe : correctif des accents (et d'animations si demandé)
    if ($ExeAModifier) {
        if (-not $manifesteActuel.Contains('zeus.exe')) {
            Copy-Fichier $exe.FullName (Join-Path $DossierSauvegarde 'Zeus.exe')
            Add-Manifeste 'R' 'Zeus.exe'
        }
        [IO.File]::WriteAllBytes($exe.FullName, $ExeCible)
    }
    if ($PatchExe.Count -gt 0) { Write-Host 'Zeus.exe : affichage des accents corrigé.' }
    if ($AnimationAppliquee) { Write-Host 'Zeus.exe : correctif d''animations appliqué.' }
    if ($VarianteHD) { Write-Host "Mod grand écran installé : $($VarianteHD.Nom)." }
    elseif ($GarderImagesHD) { Write-Host 'Mod grand écran déjà installé : conservé.' }
} catch {
    Write-Progress -Activity 'Installation des fichiers français' -Completed
    Write-Host ''
    Write-Host "L'installation a échoué : $($_.Exception.Message)" -ForegroundColor Red
    Write-Host 'Lancez DESINSTALLER.bat pour revenir à la version anglaise, puis réessayez.' -ForegroundColor Yellow
    Fin 1
}

Write-Host ''
Write-Host 'Installation terminée ! Le jeu est maintenant en français.' -ForegroundColor Green
Write-Host ''
Write-Host 'Conseils :'
if ((Get-PlateformeDossier $DossierJeu) -eq 'Steam') {
    Write-Host ' - Dans Steam, n''utilisez pas « Vérifier l''intégrité des fichiers du jeu » : cela remettrait les fichiers anglais.'
    Write-Host '   (Si cela arrive, ou après une mise à jour Steam du jeu, relancez simplement INSTALLER.bat.)'
} else {
    Write-Host ' - Dans GOG Galaxy, n''utilisez pas « Vérifier / Réparer » sur ce jeu : cela remettrait les fichiers anglais.'
    Write-Host '   (Si cela arrive, relancez simplement INSTALLER.bat.)'
}
Write-Host ' - Pour revenir à l''anglais : lancez DESINSTALLER.bat.'
Fin 0
