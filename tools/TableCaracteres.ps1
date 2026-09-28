# Recherche de la table « caractère -> glyphe de police » dans Zeus.exe.
# La table fait 224 octets (caractères 0x20 à 0xFF) ; on la repère aux lettres a..z (glyphes 1..26)
# et A..Z (glyphes 27..52) consécutives.

if (-not ('ZeusTableScan' -as [type])) {
    Add-Type -TypeDefinition @'
public static class ZeusTableScan {
    public static int[] Find(byte[] b) {
        var r = new System.Collections.Generic.List<int>();
        for (int o = 0; o + 256 <= b.Length; o++) {
            bool ok = true;
            for (int i = 0; i < 26 && ok; i++)
                if (b[o + 0x61 + i] != 1 + i || b[o + 0x41 + i] != 27 + i) ok = false;
            if (ok) r.Add(o + 0x20);
        }
        return r.ToArray();
    }
}
'@
}

$script:TailleTable = 224

# Retourne l'offset (dans le fichier) du début de la table, ou lève une erreur si elle est absente ou ambiguë
function Find-TableCaracteres([byte[]]$exe, [string]$nom) {
    $r = [ZeusTableScan]::Find($exe)
    if ($r.Count -ne 1) { throw "$nom : table de caractères introuvable ou ambiguë ($($r.Count) résultat(s))" }
    return $r[0]
}

function Get-TableCaracteres([string]$cheminExe) {
    $b = [IO.File]::ReadAllBytes($cheminExe)
    $o = Find-TableCaracteres $b $cheminExe
    $t = New-Object byte[] $script:TailleTable
    [Array]::Copy($b, $o, $t, 0, $script:TailleTable)
    return , $t
}
