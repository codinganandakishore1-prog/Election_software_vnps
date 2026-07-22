# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — Windows desktop voting node (SRS: PyInstaller packaging).

Build on Windows (or GitHub Actions windows-latest):
  pip install -r desktop/requirements.txt pyinstaller
  set PYTHONPATH=desktop;shared
  pyinstaller desktop/packaging/ElectionVotingNode.spec

Output: dist/ElectionVotingNode/ElectionVotingNode.exe
"""

from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules

# SPEC is injected by PyInstaller as the absolute path to this .spec file.
ROOT = Path(SPEC).resolve().parents[2]
DESKTOP = ROOT / "desktop"
SHARED = ROOT / "shared"

# Fail the build early if critical packages are missing from the source tree
# (e.g. a bad copy that dropped desktop/app/data/).
_required = [
    DESKTOP / "run_voting_app.py",
    DESKTOP / "app" / "__init__.py",
    DESKTOP / "app" / "main.py",
    DESKTOP / "app" / "data" / "__init__.py",
    DESKTOP / "app" / "data" / "election_store.py",
    DESKTOP / "app" / "exceptions.py",
    DESKTOP / "assets" / "backgrounds",
    SHARED / "election_platform" / "__init__.py",
]
_missing = [str(path) for path in _required if not path.exists()]
if _missing:
    raise SystemExit(
        "ElectionVotingNode.spec: required source files are missing:\n  - "
        + "\n  - ".join(_missing)
        + "\nDo not exclude desktop/app/data/ when copying the project."
    )

datas = [
    (str(DESKTOP / "assets"), "assets"),
]
binaries = []

# Ensure PyInstaller resolves desktop/app (package), not a root app.py module.
import sys

_desktop = str(DESKTOP)
_shared = str(SHARED)
for _path in (_shared, _desktop):
    while _path in sys.path:
        sys.path.remove(_path)
sys.path.insert(0, _desktop)
sys.path.insert(1, _shared)

# First-party: collect every submodule so lazy imports cannot be omitted.
hiddenimports = []
hiddenimports += collect_submodules("app")
hiddenimports += collect_submodules("election_platform")
if "app.data" not in hiddenimports or "app.data.election_store" not in hiddenimports:
    raise SystemExit(
        "ElectionVotingNode.spec: collect_submodules('app') did not find app.data. "
        "Check that desktop/app/data/ exists and is not shadowed by a root app.py."
    )

# Third-party packages that load plugins / data / binary extensions dynamically.
# collect_all pulls datas + binaries + hiddenimports for each.
for package in (
    "customtkinter",
    "certifi",
    "PIL",
    "sqlalchemy",
    "pydantic",
    "pydantic_core",
    "pydantic_settings",
    "fakeredis",
    "requests",
    "urllib3",
    "charset_normalizer",
    "idna",
    "darkdetect",
):
    try:
        pkg_datas, pkg_binaries, pkg_hidden = collect_all(package)
    except Exception as exc:  # pragma: no cover - defensive for optional names
        raise SystemExit(
            f"ElectionVotingNode.spec: collect_all({package!r}) failed: {exc}\n"
            "Install desktop/requirements.txt (and greenlet) before building."
        ) from exc
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hidden

# Extra modules Analysis commonly misses on Windows.
hiddenimports += collect_submodules("PIL")
hiddenimports += collect_submodules("fakeredis")
hiddenimports += [
    "PIL._tkinter_finder",
    "PIL.Image",
    "PIL.PngImagePlugin",
    "PIL.JpegImagePlugin",
    "PIL.GifImagePlugin",
    "PIL.BmpImagePlugin",
    "PIL.WebPImagePlugin",
    "greenlet",
    "redis",
    "dotenv",
    "packaging",
    "packaging.version",
    "annotated_types",
    "darkdetect._windows_detect",
    "sqlalchemy.dialects.sqlite",
    "sqlalchemy.dialects.sqlite.pysqlite",
    "sqlalchemy.dialects.mysql",
    "sqlalchemy.dialects.mysql.pymysql",
    "pymysql",
    "pymysql.constants",
    "pymysql.converters",
    "pymysql.cursors",
    "tkinter",
    "tkinter.ttk",
    "tkinter.messagebox",
    "sqlite3",
    "charset_normalizer.md",
]

a = Analysis(
    [str(DESKTOP / "run_voting_app.py")],
    pathex=[str(DESKTOP), str(SHARED)],  # desktop first — package app/, not root app.py
    binaries=binaries,
    datas=datas,
    hiddenimports=sorted(set(hiddenimports)),
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
