# Build ElectionVotingNode.exe for Windows (SRS: PyInstaller).
# Run in PowerShell from anywhere:
#   .\deployment\scripts\build_desktop_windows.ps1

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Root

python -m pip install --upgrade pip
python -m pip install -r desktop\requirements.txt pyinstaller

$env:PYTHONPATH = "$Root\shared;$Root\desktop"
python -m PyInstaller --noconfirm --clean desktop\packaging\ElectionVotingNode.spec

Write-Host ""
Write-Host "Build complete:"
Write-Host "  dist\ElectionVotingNode\ElectionVotingNode.exe"
Write-Host "Copy the entire ElectionVotingNode folder to voting PCs."
