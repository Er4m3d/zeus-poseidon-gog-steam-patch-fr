# Compile l'installateur avec le compilateur C# fourni avec Windows (.NET Framework 4) : rien à installer.
#   powershell -ExecutionPolicy Bypass -File .\build.ps1        ->  dist\ZeusPatchFR.exe
$ErrorActionPreference = 'Stop'
$racine = $PSScriptRoot
$csc = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
if (-not (Test-Path $csc)) { $csc = Join-Path $env:WINDIR 'Microsoft.NET\Framework\v4.0.30319\csc.exe' }
foreach ($f in 'data\plan.txt', 'data\patch_exe.txt') {
    if (-not (Test-Path (Join-Path $racine $f))) { throw "$f absent : lancez d'abord les générateurs de tools\ (voir README)." }
}
$dist = Join-Path $racine 'dist'
New-Item -ItemType Directory -Path $dist -Force | Out-Null
$sortie = Join-Path $dist 'ZeusPatchFR.exe'
$sources = Get-ChildItem (Join-Path $racine 'src') -Filter *.cs | ForEach-Object { $_.FullName }
& $csc /nologo /target:winexe /optimize+ /codepage:65001 "/out:$sortie" `
    "/win32manifest:$(Join-Path $racine 'src\app.manifest')" `
    "/win32icon:$(Join-Path $racine 'src\app.ico')" `
    "/resource:$(Join-Path $racine 'data\plan.txt'),ZeusPatchFR.plan.txt" `
    "/resource:$(Join-Path $racine 'data\patch_exe.txt'),ZeusPatchFR.patch_exe.txt" `
    /reference:System.dll /reference:System.Drawing.dll /reference:System.Windows.Forms.dll `
    $sources
if ($LASTEXITCODE) { throw "Échec de la compilation ($LASTEXITCODE)." }
'{0}  ({1:N0} Ko)' -f $sortie, ((Get-Item $sortie).Length / 1KB)
