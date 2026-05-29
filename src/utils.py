"""Common utility functions."""

import os
import shutil
from decimal import Decimal, ROUND_HALF_UP


def ensure_dir(path: str) -> None:
    """Create directory recursively if it does not exist."""
    os.makedirs(path, exist_ok=True)


def write_text_lf(filepath: str, content: str, force_lf: bool = True) -> None:
    """Write a text file, optionally enforcing LF line endings.

    Args:
        filepath: Output file path.
        content: Text content to write.
        force_lf: If True, force LF line endings; otherwise use the OS default.
    """
    ensure_dir(os.path.dirname(filepath))
    if force_lf:
        with open(filepath, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
    else:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)


def to_int_round_half_up(value: float) -> int:
    """Round to the nearest integer using ROUND_HALF_UP (standard rounding)."""
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def format_number(value: float):
    """Return int if value is a whole number, otherwise the original float."""
    if value == int(value):
        return int(value)
    return value


def collect_files(root_dir: str, extensions: list[str]) -> list[str]:
    """Recursively collect all files under root_dir matching the given extensions."""
    files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for f in filenames:
            if os.path.splitext(f)[1].lower() in extensions:
                files.append(os.path.join(dirpath, f))
    return files


def get_song_dirs(songs_dir: str) -> list[str]:
    """Return all subdirectory paths under songs_dir (one per song)."""
    return [
        os.path.join(songs_dir, d)
        for d in os.listdir(songs_dir)
        if os.path.isdir(os.path.join(songs_dir, d))
    ]


def copy_unprocessed(
    songs_dir: str,
    output_dir: str,
    *,
    skip_extensions: set[str] | None = None,
    skip_names: set[str] | None = None,
) -> int:
    """Copy files that are not processed (images, etc.) to the output directory.

    Args:
        songs_dir: Source songs directory.
        output_dir: Output directory.
        skip_extensions: File extensions to skip (already processed).
        skip_names: Exact filenames to skip (e.g. "songlist").

    Returns:
        Number of files copied.
    """
    skip_extensions = skip_extensions or set()
    skip_names = skip_names or set()
    copied = 0

    for dirpath, _, filenames in os.walk(songs_dir):
        for f in filenames:
            if f in skip_names:
                continue
            if os.path.splitext(f)[1].lower() in skip_extensions:
                continue

            src = os.path.join(dirpath, f)
            rel = os.path.relpath(src, songs_dir)
            dst = os.path.join(output_dir, rel)
            ensure_dir(os.path.dirname(dst))
            shutil.copy2(src, dst)
            copied += 1

    return copied
