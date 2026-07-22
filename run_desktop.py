"""Legacy entry point — launches the refactored desktop application.

Renamed from app.py so it does not shadow the desktop/app package
(required for PyInstaller and PYTHONPATH=desktop imports).
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / "shared"), str(ROOT / "desktop")]

from app.main import main  # noqa: E402

if __name__ == "__main__":
    main()
