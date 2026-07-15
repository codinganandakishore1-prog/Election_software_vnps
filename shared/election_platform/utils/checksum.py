"""Checksum utilities for configuration packages."""

from __future__ import annotations

import hashlib
from pathlib import Path

CHECKSUM_FILENAME = "Checksum.sha256"


def compute_directory_checksum(directory: Path, *, checksum_filename: str = CHECKSUM_FILENAME) -> str:
    """Compute a SHA-256 digest over all files in a directory.

    Each file contributes its relative POSIX path followed by its raw bytes.
    The checksum file itself is excluded from the digest.
    """
    digest = hashlib.sha256()
    for file_path in sorted(directory.rglob("*")):
        if not file_path.is_file() or file_path.name == checksum_filename:
            continue
        digest.update(file_path.relative_to(directory).as_posix().encode("utf-8"))
        digest.update(file_path.read_bytes())
    return digest.hexdigest()
