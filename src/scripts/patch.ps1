#Requires -Version 5.1
<#
    Patch de traduction française - Le Maître de l'Olympe : Zeus & Poséidon (version GOG)

    Installation   : powershell -ExecutionPolicy Bypass -File patch.ps1
    Désinstallation: powershell -ExecutionPolicy Bypass -File patch.ps1 -Desinstaller
    Options        : -DossierJeu "<chemin>"  force le dossier du jeu
                     -Oui                    ne pose aucune question (mode silencieux)
#>
param(
    [string]$DossierJeu,
    [switch]$Desinstaller,
    [switch]$Oui
)

$ErrorActionPreference = 'Stop'
$VersionPatch   = '1.3'
$RacinePatch    = Split-Path -Parent $PSScriptRoot
$DossierFichiers = Join-Path $RacinePatch 'fichiers'
$ListeARetirer  = Join-Path $PSScriptRoot 'fichiers_anglais_a_retirer.txt'
$NomSauvegarde  = 'Sauvegarde_VO_Patch_FR'
$GogId          = '1207659039'

function Titre($texte) {
    Write-Host ''
    Write-Host ('=' * 70) -ForegroundColor DarkYellow
    Write-Host "  $texte" -ForegroundColor Yellow
    Write-Host ('=' * 70) -ForegroundColor DarkYellow
    Write-Host ''
}

function Fin($code) {
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

function Find-DossierJeu {
    $candidats = @()
    foreach ($cle in "HKLM:\SOFTWARE\WOW6432Node\GOG.com\Games\$GogId", "HKLM:\SOFTWARE\GOG.com\Games\$GogId") {
        try { $candidats += (Get-ItemProperty -LiteralPath $cle -ErrorAction Stop).path } catch {}
    }
    foreach ($cle in "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\${GogId}_is1",
                     "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\${GogId}_is1") {
        try { $candidats += (Get-ItemProperty -LiteralPath $cle -ErrorAction Stop).InstallLocation } catch {}
    }
    $candidats += @(
        (Join-Path $env:ProgramFiles 'GOG Galaxy\Games\Zeus and Poseidon'),
        (Join-Path ${env:ProgramFiles(x86)} 'GOG Galaxy\Games\Zeus and Poseidon'),
        'C:\GOG Games\Zeus and Poseidon',
        (Split-Path -Parent $RacinePatch)   # patch extrait directement dans le dossier du jeu
    )
    foreach ($c in $candidats) {
        if ($c -and (Test-DossierJeu $c)) { return (Resolve-Path -LiteralPath $c).Path.TrimEnd('\') }
    }
    return $null
}

function Select-DossierJeu {
    Add-Type -AssemblyName System.Windows.Forms
    $dlg = New-Object System.Windows.Forms.FolderBrowserDialog
    $dlg.Description = "Sélectionnez le dossier d'installation GOG de « Zeus and Poseidon » (celui qui contient Zeus.exe)"
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
Titre "Patch FR v$VersionPatch - Le Maître de l'Olympe : Zeus & Poséidon (GOG) - $action"

if (-not $Desinstaller -and -not (Test-Path -LiteralPath (Join-Path $DossierFichiers 'Zeus_Text.eng'))) {
    Erreur "Le dossier « fichiers » du patch est introuvable. Avez-vous bien extrait tout le ZIP avant de lancer l'installation ?"
}

# 1. Dossier du jeu
if ($DossierJeu) {
    $DossierJeu = $DossierJeu.Trim('"').TrimEnd('\')
    if (-not (Test-DossierJeu $DossierJeu)) { Erreur "Le dossier « $DossierJeu » ne contient pas Zeus and Poseidon." }
} else {
    $DossierJeu = Find-DossierJeu
    if ($DossierJeu) {
        Write-Host "Jeu détecté dans : $DossierJeu" -ForegroundColor Green
        if (-not (Confirmer 'Utiliser ce dossier ?')) { $DossierJeu = $null }
    } else {
        Write-Host "Le jeu n'a pas été trouvé automatiquement." -ForegroundColor Yellow
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
$FichierPatchExe = Join-Path $PSScriptRoot 'zeus_exe_patch.txt'
$PatchExe = @()
$PatchExeAFaire = @()
if (Test-Path -LiteralPath $FichierPatchExe) {
    $versOctets = { param($h) [byte[]]@(for ($j = 0; $j -lt $h.Length; $j += 2) { [Convert]::ToByte($h.Substring($j, 2), 16) }) }
    foreach ($l in [IO.File]::ReadAllLines($FichierPatchExe)) {
        if ($l -match '^([0-9A-F]+) ([0-9A-F]+) ([0-9A-F]+)$') {
            $PatchExe += [pscustomobject]@{ Offset = [Convert]::ToInt64($Matches[1], 16); Origine = (& $versOctets $Matches[2]); Nouveau = (& $versOctets $Matches[3]) }
        }
    }
    $octetsExe = [IO.File]::ReadAllBytes($exe.FullName)
    $egal = { param($off, $attendu) if ($off + $attendu.Length -gt $octetsExe.Length) { return $false }; for ($j = 0; $j -lt $attendu.Length; $j++) { if ($octetsExe[$off + $j] -ne $attendu[$j]) { return $false } }; return $true }
    foreach ($p in $PatchExe) {
        if (& $egal $p.Offset $p.Nouveau) { continue }
        if (& $egal $p.Offset $p.Origine) { $PatchExeAFaire += $p; continue }
        Erreur 'Ce Zeus.exe n''est pas reconnu : ce patch est prévu pour la version GOG 2.1.4.0. Aucune modification n''a été faite.'
    }
}
$TableFr = $PatchExe.Count -gt 0

$manifesteActuel = Read-Manifeste
if ($manifesteActuel.Count -gt 0) {
    Write-Host 'Le patch FR est déjà installé : les fichiers français vont être réinstallés (la sauvegarde anglaise existante est conservée).' -ForegroundColor Yellow
}

$fichiers = @(Get-ChildItem -LiteralPath $DossierFichiers -Recurse -File)
$aRetirer = @()
if (Test-Path -LiteralPath $ListeARetirer) {
    $aRetirer = @([IO.File]::ReadAllLines($ListeARetirer, [Text.Encoding]::UTF8) | Where-Object { $_.Trim() })
}
$tailleMo = [Math]::Round((($fichiers | Measure-Object Length -Sum).Sum) / 1MB)
Write-Host "Le patch va installer $($fichiers.Count) fichiers français ($tailleMo Mo)."
Write-Host "Les fichiers anglais remplacés seront sauvegardés dans : $DossierSauvegarde"
Write-Host ''
if (-not (Confirmer 'Lancer l''installation ?')) { Write-Host 'Annulé.'; Fin 0 }

$libre = (Get-PSDrive -Name ($DossierJeu.Substring(0, 1))).Free
if ($libre -and $libre -lt 2 * ($tailleMo * 1MB)) { Erreur "Espace disque insuffisant (il faut environ $(2 * $tailleMo) Mo libres)." }

New-Item -ItemType Directory -Path $DossierSauvegarde -Force | Out-Null
$prefixe = $DossierFichiers.TrimEnd('\').Length + 1

try {
    # Mise à jour depuis une version précédente du patch : suppression des fichiers ajoutés
    # qui n'existent plus sous ce nom (ex. noms accentués de la v1.0)
    if ($manifesteActuel.Count -gt 0) {
        $nouveaux = @{}
        foreach ($f in $fichiers) { $nouveaux[$f.FullName.Substring($prefixe).ToLowerInvariant()] = $true }
        if ($TableFr) { $nouveaux['zeus.exe'] = $true }
        $obsoletes = @($manifesteActuel.Keys | Where-Object { $manifesteActuel[$_].Type -in 'N', 'R' -and -not $nouveaux.ContainsKey($_) })
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
            # déjà sauvegardé lors d'une installation précédente (fichier remis par GOG Galaxy)
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
        $rel = $f.FullName.Substring($prefixe)
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
        Copy-Fichier $f.FullName $cible
    }
    Write-Progress -Activity 'Installation des fichiers français' -Completed

    # c) Correctif des accents dans Zeus.exe
    if ($PatchExeAFaire.Count -gt 0) {
        if (-not $manifesteActuel.Contains('zeus.exe')) {
            Copy-Fichier $exe.FullName (Join-Path $DossierSauvegarde 'Zeus.exe')
            Add-Manifeste 'R' 'Zeus.exe'
        }
        $fs = [IO.File]::Open($exe.FullName, [IO.FileMode]::Open, [IO.FileAccess]::Write)
        try { foreach ($p in $PatchExeAFaire) { $fs.Position = $p.Offset; $fs.Write($p.Nouveau, 0, $p.Nouveau.Length) } } finally { $fs.Dispose() }
        Write-Host 'Zeus.exe : affichage des accents corrigé.'
    }
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
Write-Host ' - Dans GOG Galaxy, n''utilisez pas « Vérifier / Réparer » sur ce jeu : cela remettrait les fichiers anglais.'
Write-Host '   (Si cela arrive, relancez simplement INSTALLER.bat.)'
Write-Host ' - Pour revenir à l''anglais : lancez DESINSTALLER.bat.'
Fin 0
