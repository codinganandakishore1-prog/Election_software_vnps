"""Import smoke test used before PyInstaller builds.

Run from desktop/ with:
  set PYTHONPATH=desktop;shared   (Windows)
  PYTHONPATH=desktop:shared       (Unix)

  python packaging/verify_imports.py
"""

from __future__ import annotations

import importlib
import io
import sys
from pathlib import Path

MODULES = [
    # First-party entry / packages
    "app",
    "app.main",
    "app.runtime_paths",
    "app.exceptions",
    "app.utils",
    "app.config.settings",
    "app.dependencies.container",
    "app.data",
    "app.data.election_store",
    "app.database.session",
    "app.database.init_db",
    "app.models",
    "app.models.local_vote",
    "app.models.queue",
    "app.models.desktop_setting",
    "app.ui.background_manager",
    "app.ui.screens.voting_screen",
    "app.ui.screens.admin_login",
    "app.ui.screens.admin_panel",
    "app.sync.queue_manager",
    "app.sync.sync_manager",
    "app.sync.vote_serializer",
    "app.health.heartbeat_manager",
    "app.health.recovery_manager",
    "election_platform",
    "election_platform.config.base",
    "election_platform.logging.setup",
    "election_platform.utils.checksum",
    # Third-party freeze traps
    "customtkinter",
    "darkdetect",
    "PIL",
    "PIL.Image",
    "PIL.PngImagePlugin",
    "PIL.JpegImagePlugin",
    "PIL._tkinter_finder",
    "sqlalchemy",
    "sqlalchemy.dialects.sqlite",
    "sqlalchemy.dialects.sqlite.pysqlite",
    "greenlet",
    "pymysql",
    "fakeredis",
    "redis",
    "requests",
    "urllib3",
    "certifi",
    "charset_normalizer",
    "idna",
    "pydantic",
    "pydantic_core",
    "pydantic_settings",
    "dotenv",
    "tkinter",
    "sqlite3",
]

# Fallback colors if an on-disk background cannot be opened (corrupt USB copy, etc.)
_BG_FALLBACKS = {
    "default_dark_bg.png": (24, 24, 32),
    "default_light_bg.png": (240, 240, 245),
    "default_welcome_bg.png": (30, 60, 100),
}


def _check_pillow() -> None:
    """Prove Pillow plugins work. Repair on-disk backgrounds if needed."""
    from PIL import Image

    # Required: in-memory round-trip (never depends on USB/disk asset integrity).
    for fmt in ("PNG", "JPEG"):
        buffer = io.BytesIO()
        Image.new("RGB", (8, 8), color=(20, 40, 60)).save(buffer, format=fmt)
        buffer.seek(0)
        with Image.open(buffer) as image:
            image.load()
            if image.size != (8, 8):
                raise RuntimeError(f"Pillow {fmt} round-trip produced wrong size")

    assets = Path(__file__).resolve().parents[1] / "assets" / "backgrounds"
    assets.mkdir(parents=True, exist_ok=True)

    for name, color in _BG_FALLBACKS.items():
        path = assets / name
        needs_rewrite = True
        if path.is_file() and path.stat().st_size > 32:
            try:
                with Image.open(path) as image:
                    image.load()
                needs_rewrite = False
            except Exception as exc:  # noqa: BLE001 - repair any unreadable asset
                print(f"WARN: repairing unreadable background {path.name}: {exc}")

        if needs_rewrite:
            Image.new("RGB", (1024, 576), color=color).save(path, format="PNG")
            print(f"OK: wrote valid PNG {path.name}")

        # Confirm the file is now readable as an image.
        with Image.open(path) as image:
            image.load()


def main() -> int:
    app_mod = importlib.import_module("app")
    if not hasattr(app_mod, "__path__"):
        print("FAIL: 'app' imported but is not a package:", getattr(app_mod, "__file__", None))
        print("Remove any root-level app.py that shadows desktop/app/.")
        return 1

    failed: list[str] = []
    for name in MODULES:
        try:
            importlib.import_module(name)
        except Exception as exc:  # noqa: BLE001 - report all import failures
            failed.append(f"{name}: {type(exc).__name__}: {exc}")

    if failed:
        print("FAIL: import smoke test")
        for line in failed:
            print(" ", line)
        return 1

    try:
        _check_pillow()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: Pillow check: {type(exc).__name__}: {exc}")
        return 1

    try:
        from sqlalchemy import create_engine
        import certifi
        import fakeredis

        create_engine("sqlite:///:memory:").connect().close()
        fakeredis.FakeStrictRedis(decode_responses=True).ping()
        with open(certifi.where(), "rb") as handle:
            if not handle.read(1):
                print("FAIL: certifi CA bundle is empty")
                return 1
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: runtime dependency check: {type(exc).__name__}: {exc}")
        return 1

    print("OK: import smoke test passed")
    print("  app package:", app_mod.__file__)
    print("  python:", sys.executable)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
