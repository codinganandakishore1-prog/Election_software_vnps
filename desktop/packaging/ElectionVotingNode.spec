# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — Windows desktop voting node (SRS: PyInstaller packaging).

Build on Windows (or GitHub Actions windows-latest):
  pip install -r desktop/requirements.txt pyinstaller
  set PYTHONPATH=shared;desktop
  pyinstaller desktop/packaging/ElectionVotingNode.spec

Output: dist/ElectionVotingNode/ElectionVotingNode.exe
"""

from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_data_files

# SPEC is injected by PyInstaller as the absolute path to this .spec file.
ROOT = Path(SPEC).resolve().parents[2]
DESKTOP = ROOT / "desktop"
SHARED = ROOT / "shared"

datas = [
    (str(DESKTOP / "assets"), "assets"),
]
binaries = []
hiddenimports = [
    "election_platform",
    "election_platform.config",
    "election_platform.config.base",
    "election_platform.logging",
    "election_platform.logging.setup",
    "election_platform.utils.checksum",
    "election_platform.enums",
    "election_platform.schemas",
    "PIL._tkinter_finder",
    "customtkinter",
    "sqlalchemy.dialects.sqlite",
    "pymysql",
    "fakeredis",
    "pydantic_settings",
]

for package in ("customtkinter", "certifi"):
    pkg_datas, pkg_binaries, pkg_hidden = collect_all(package)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hidden

datas += collect_data_files("customtkinter")

a = Analysis(
    [str(DESKTOP / "run_voting_app.py")],
    pathex=[str(SHARED), str(DESKTOP)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

# onedir is more reliable than onefile for CustomTkinter/Tk on school PCs.
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ElectionVotingNode",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # GUI app — no black console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="ElectionVotingNode",
)
