# Conversion des textes du jeu en ASCII pur (é -> e, œ -> oe, « » -> ", etc.)
# pour les polices du jeu qui affichent mal les caractères accentués.
# Les fichiers binaires .eng sont reconstruits : les offsets d'index sont recalculés.

$script:Cp1252 = [Text.Encoding]::GetEncoding(1252)
$script:Speciaux = @{
    0x80 = 'EUR'; 0x82 = "'"; 0x84 = '"'; 0x85 = '...'; 0x8C = 'OE'; 0x91 = "'"; 0x92 = "'"
    0x93 = '"'; 0x94 = '"'; 0x95 = '-'; 0x96 = '-'; 0x97 = '-'; 0x99 = 'TM'; 0x9C = 'oe'
    0xA0 = ' '; 0xA9 = '(c)'; 0xAB = '"'; 0xAE = '(R)'; 0xB0 = 'o'; 0xB2 = '2'; 0xB3 = '3'
    0xB7 = '.'; 0xB9 = '1'; 0xBB = '"'; 0xBC = '1/4'; 0xBD = '1/2'; 0xBE = '3/4'
    0xC6 = 'AE'; 0xD7 = 'x'; 0xDF = 'ss'; 0xE6 = 'ae'
}
$script:Table = New-Object 'byte[][]' 256
$script:Inconnus = @{}
for ($i = 0; $i -lt 256; $i++) {
    if ($i -lt 128) { $script:Table[$i] = [byte[]]@($i); continue }
    if ($script:Speciaux.ContainsKey($i)) { $s = $script:Speciaux[$i] }
    else {
        $c = $script:Cp1252.GetString([byte[]]@($i)).Normalize([Text.NormalizationForm]::FormD)
        $s = -join ($c.ToCharArray() | Where-Object { [int]$_ -lt 128 })
        if (-not $s) { $s = '?' }
    }
    $script:Table[$i] = [Text.Encoding]::ASCII.GetBytes($s)
}

# Convertit un bloc d'octets CP1252. Retourne @{ Octets = byte[]; Map = int[] (ancienne position -> nouvelle) }
function Convert-OctetsAscii([byte[]]$src) {
    $out = New-Object 'System.Collections.Generic.List[byte]' ($src.Length + 1024)
    $map = New-Object 'int[]' ($src.Length + 1)
    $ponct = [byte[]][char[]]':;!?'
    for ($i = 0; $i -lt $src.Length; $i++) {
        $map[$i] = $out.Count
        $b = $src[$i]
        if ($b -lt 128) { $out.Add($b); continue }
        if ($b -eq 0xA0) {
            # espace insécable de la typographie française : supprimée autour de la ponctuation ( « mot » , mot ! )
            $suiv = if ($i + 1 -lt $src.Length) { $src[$i + 1] } else { 0 }
            $prec = if ($i -gt 0) { $src[$i - 1] } else { 0 }
            if ($ponct -contains $suiv -or $suiv -eq 0xBB -or $prec -eq 0xAB) { continue }
        }
        if ($script:Table[$b].Length -eq 1 -and $script:Table[$b][0] -eq 0x3F) { $script:Inconnus[[int]$b] = 1 + [int]$script:Inconnus[[int]$b] }
        $out.AddRange($script:Table[$b])
    }
    $map[$src.Length] = $out.Count
    return @{ Octets = $out.ToArray(); Map = $map }
}

function ConvertTo-NomAscii([string]$nom) {
    $b = $script:Cp1252.GetBytes($nom)
    return [Text.Encoding]::ASCII.GetString((Convert-OctetsAscii $b).Octets) -replace '"', "'"
}

function Assert-DebutChaine([byte[]]$data, [int]$off, [string]$quoi) {
    if ($off -gt 0 -and $data[$off - 1] -ne 0) { throw "$quoi : l'offset $off ne pointe pas sur un début de chaîne" }
}

function Write-Octets([string]$chemin, [byte[]]$a, [byte[]]$b) {
    $fs = [IO.File]::Create($chemin)
    try { $fs.Write($a, 0, $a.Length); $fs.Write($b, 0, $b.Length) } finally { $fs.Dispose() }
}

# Zeus_Text.eng / Zeus_Editor_Text.eng : en-tête 28 octets + 1000 x (offset, nb) + chaînes terminées par 0
function Convert-FichierTexteEng([string]$chemin) {
    $b = [IO.File]::ReadAllBytes($chemin)
    $debut = 28 + 8 * 1000
    $data = New-Object byte[] ($b.Length - $debut); [Array]::Copy($b, $debut, $data, 0, $data.Length)
    $r = Convert-OctetsAscii $data
    $entete = New-Object byte[] $debut; [Array]::Copy($b, $entete, $debut)
    for ($i = 0; $i -lt 1000; $i++) {
        $pos = 28 + 8 * $i
        $off = [BitConverter]::ToInt32($entete, $pos)
        if ($off -lt 0 -or $off -gt $data.Length) { throw "$chemin : offset d'index invalide ($off)" }
        Assert-DebutChaine $data $off $chemin
        [Array]::Copy([BitConverter]::GetBytes([int]$r.Map[$off]), 0, $entete, $pos, 4)
    }
    Write-Octets $chemin $entete $r.Octets
    return @{ Avant = $b.Length; Apres = $debut + $r.Octets.Length }
}

# Zeus_MM.eng : en-tête 24 octets + 1000 entrées de 80 octets + chaînes.
# Offsets de texte aux positions 56 (vidéo), 68 (titre), 72 (sous-titre), 76 (contenu) de chaque entrée.
function Convert-FichierMessagesEng([string]$chemin) {
    $b = [IO.File]::ReadAllBytes($chemin)
    $debut = 24 + 80 * 1000
    $data = New-Object byte[] ($b.Length - $debut); [Array]::Copy($b, $debut, $data, 0, $data.Length)
    $r = Convert-OctetsAscii $data
    $entete = New-Object byte[] $debut; [Array]::Copy($b, $entete, $debut)
    for ($i = 0; $i -lt 1000; $i++) {
        foreach ($champ in 56, 68, 72, 76) {
            $pos = 24 + 80 * $i + $champ
            $off = [BitConverter]::ToInt32($entete, $pos)
            if ($off -eq 0) { continue }
            if ($off -lt 0 -or $off -gt $data.Length) { throw "$chemin : offset invalide ($off) entrée $i" }
            Assert-DebutChaine $data $off "$chemin entrée $i"
            [Array]::Copy([BitConverter]::GetBytes([int]$r.Map[$off]), 0, $entete, $pos, 4)
        }
    }
    Write-Octets $chemin $entete $r.Octets
    return @{ Avant = $b.Length; Apres = $debut + $r.Octets.Length }
}

# Fichiers texte (eventmsg, textes d'aventure) : conversion directe
function Convert-FichierTexteBrut([string]$chemin) {
    $b = [IO.File]::ReadAllBytes($chemin)
    $r = Convert-OctetsAscii $b
    [IO.File]::WriteAllBytes($chemin, $r.Octets)
    return @{ Avant = $b.Length; Apres = $r.Octets.Length }
}
