"""Resolve resource and writable paths for source runs and frozen EXEs."""

from __future__ import annotations

import sys
from pathlib import Path


def is_frozen() -> bool:
    """True when running as a PyInstaller-built executable."""
    return bool(getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"))


def resource_root() -> Path:
    """Read-only bundled assets (backgrounds, themes included in the build)."""
    if is_frozen():
        return Path(sys._MEIPASS)
    # desktop/app/runtime_paths.py → desktop/
    return Path(__file__).resolve().parents[1]


def data_root() -> Path:
    """Writable root next to the EXE (portable school USB / folder installs)."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    # desktop/app/runtime_paths.py → desktop/
    return Path(__file__).resolve().parents[1]
