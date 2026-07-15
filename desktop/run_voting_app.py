"""PyInstaller entry point for the Windows desktop voting application."""

from __future__ import annotations


def main() -> None:
    from app.main import main as run_app

    run_app()


if __name__ == "__main__":
    main()
