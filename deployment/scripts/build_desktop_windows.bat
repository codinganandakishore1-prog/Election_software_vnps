@echo off
REM Build ElectionVotingNode.exe for Windows (SRS: PyInstaller).
REM Requires: Python 3.10+ (3.12 recommended), Windows 10/11.
REM Windows 7/8 are listed in the SRS but are not supported by current Python runtimes.

setlocal
cd /d "%~dp0..\.."

python -m pip install --upgrade pip
python -m pip install -r desktop\requirements.txt pyinstaller

set PYTHONPATH=%CD%\shared;%CD%\desktop
python -m PyInstaller --noconfirm --clean desktop\packaging\ElectionVotingNode.spec

echo.
echo Build complete:
echo   dist\ElectionVotingNode\ElectionVotingNode.exe
echo Copy the entire ElectionVotingNode folder to voting PCs.
endlocal
