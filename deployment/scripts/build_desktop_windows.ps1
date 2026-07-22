# Build ElectionVotingNode.exe for Windows (SRS: PyInstaller).
# Run in PowerShell from anywhere:
#   .\deployment\scripts\build_desktop_windows.ps1

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Root

Write-Host ""
Write-Host "=== Pre-build checks ==="
$required = @(
    "desktop\app\data\election_store.py",
    "desktop\run_voting_app.py",
    "shared\election_platform",
    "desktop\assets\backgrounds"
)
foreach ($rel in $required) {
    if (-not (Test-Path (Join-Path $Root $rel))) {
        throw "Missing required path: $rel. Do not exclude desktop\app\data when copying the project."
    }
}
Write-Host "OK: required source packages found."
Write-Host ""

python -m pip install --upgrade pip
python -m pip install -r desktop\requirements.txt pyinstaller

# Prefer desktop package path; never rely on a root-level app.py (that shadows app/).
$env:PYTHONPATH = "$Root\desktop;$Root\shared"

Write-Host "=== Import smoke test ==="
Push-Location (Join-Path $Root "desktop")
python packaging\verify_imports.py
if ($LASTEXITCODE -ne 0) {
    Pop-Location
    throw "Import smoke test failed. Fix missing modules before building."
}
Pop-Location

Write-Host ""
Write-Host "=== PyInstaller build ==="
python -m PyInstaller --noconfirm --clean desktop\packaging\ElectionVotingNode.spec

Write-Host ""
Write-Host "=== Post-build checks ==="
$exe = Join-Path $Root "dist\ElectionVotingNode\ElectionVotingNode.exe"
$internal = Join-Path $Root "dist\ElectionVotingNode\_internal"
if (-not (Test-Path $exe)) { throw "EXE was not created." }
if (-not (Test-Path $internal)) { throw "_internal folder missing — do not ship a lone EXE." }

Write-Host "OK: dist\ElectionVotingNode\ElectionVotingNode.exe"
Write-Host ""
Write-Host "Build complete."
Write-Host "Copy the ENTIRE ElectionVotingNode folder to voting PCs."
Write-Host "If the EXE fails to open, read: logs\startup_crash.log next to the EXE."
