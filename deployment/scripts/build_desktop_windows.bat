@echo off
REM Build ElectionVotingNode.exe for Windows (SRS: PyInstaller).
REM Requires: Python 3.10+ (3.12 recommended), Windows 10/11.
REM Windows 7/8 are listed in the SRS but are not supported by current Python runtimes.

setlocal
cd /d "%~dp0..\.."

echo.
echo === Pre-build checks ===
if not exist "desktop\app\data\election_store.py" (
  echo ERROR: desktop\app\data\ is missing.
  echo This Python package is required. Do not delete or exclude app\data
  echo when copying the project ^(that is different from desktop\data runtime folder^).
  exit /b 1
)
if not exist "desktop\run_voting_app.py" (
  echo ERROR: desktop\run_voting_app.py is missing.
  exit /b 1
)
if not exist "shared\election_platform" (
  echo ERROR: shared\election_platform is missing.
  exit /b 1
)
if not exist "desktop\assets\backgrounds" (
  echo ERROR: desktop\assets\backgrounds is missing.
  exit /b 1
)
echo OK: required source packages found.
echo.

python -m pip install --upgrade pip
python -m pip install -r desktop\requirements.txt pyinstaller
if errorlevel 1 (
  echo ERROR: pip install failed.
  exit /b 1
)

REM Prefer desktop package path; never rely on a root-level app.py (that shadows app/).
set PYTHONPATH=%CD%\desktop;%CD%\shared

echo === Import smoke test ===
pushd desktop
python packaging\verify_imports.py
if errorlevel 1 (
  echo ERROR: Import smoke test failed. Fix missing modules before building.
  popd
  exit /b 1
)
popd

echo.
echo === PyInstaller build ===
python -m PyInstaller --noconfirm --clean desktop\packaging\ElectionVotingNode.spec
if errorlevel 1 (
  echo ERROR: PyInstaller build failed.
  exit /b 1
)

echo.
echo === Post-build checks ===
if not exist "dist\ElectionVotingNode\ElectionVotingNode.exe" (
  echo ERROR: EXE was not created.
  exit /b 1
)
if not exist "dist\ElectionVotingNode\_internal" (
  echo ERROR: _internal folder missing — do not ship a lone EXE.
  exit /b 1
)

echo OK: dist\ElectionVotingNode\ElectionVotingNode.exe
echo.
echo Build complete.
echo Copy the ENTIRE ElectionVotingNode folder to voting PCs.
echo If the EXE fails to open, read: logs\startup_crash.log next to the EXE.
endlocal
