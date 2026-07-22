"""PyInstaller entry point for the Windows desktop voting application."""

from __future__ import annotations

import sys
import traceback
from pathlib import Path


def _crash_log_path() -> Path:
    """Writable log next to the EXE (frozen) or under desktop/logs (source)."""
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).resolve().parent
    else:
        base = Path(__file__).resolve().parent
    log_dir = base / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "startup_crash.log"


def main() -> None:
    from app.main import main as run_app

    run_app()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Windowed EXEs have no console — persist the traceback for operators.
        log_path = _crash_log_path()
        log_path.write_text(traceback.format_exc(), encoding="utf-8")
        try:
            import tkinter as tk
            from tkinter import messagebox

            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Election Voting Node — startup failed",
                f"The app failed to start.\n\nDetails were saved to:\n{log_path}",
            )
            root.destroy()
        except Exception:
            pass
        raise
