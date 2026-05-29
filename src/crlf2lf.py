#!/usr/bin/env python3
"""
Convert all files in a directory tree from CRLF to LF line endings.

Usage: python crlf2lf.py [folder_path]
Default folder: current directory
"""

import os
import sys


def convert_file(filepath: str) -> bool:
    """Convert a single file from CRLF to LF line endings.

    Returns True if the file was actually converted.
    """
    try:
        with open(filepath, "rb") as f:
            content = f.read()

        if b"\r\n" not in content:
            return False

        new_content = content.replace(b"\r\n", b"\n")

        with open(filepath, "wb") as f:
            f.write(new_content)

        return True
    except Exception as e:
        print(f"Error processing {filepath}: {e}", file=sys.stderr)
        return False


def main():
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]
    else:
        root_dir = os.path.dirname(os.path.abspath(__file__))

    if not os.path.isdir(root_dir):
        print(f"Error: '{root_dir}' is not a valid directory.", file=sys.stderr)
        sys.exit(1)

    print(f"Scanning for files in: {os.path.abspath(root_dir)}")

    total = 0
    converted = 0
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            total += 1
            full_path = os.path.join(dirpath, filename)
            if convert_file(full_path):
                print(f"Converted: {full_path}")
                converted += 1

    print(f"\nDone. Scanned {total} file(s), converted {converted}.")


if __name__ == "__main__":
    main()
