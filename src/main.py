"""Arcaea Speed Tool — main entry point.

Processes the entire songs/ folder structure:
  songs/
    <song_name>/
      0.aff, 1.aff, ...   → chart speed change
      base.ogg            → audio speed change
    songlist              → songlist speed change

All output is written to output_dir, preserving the original directory structure.
"""

import os
import sys

from . import utils
from .config import load_config
from . import aff_gen
from . import songlist_gen
from . import audio_gen


def main(config_path: str = "config.toml") -> None:
    """Run the full processing pipeline."""
    # ========================================================================
    # 1. Load configuration
    # ========================================================================
    print("=" * 60)
    print("  Arcaea Speed Tool — chart / audio / songlist")
    print("=" * 60)

    try:
        cfg = load_config(config_path)
    except FileNotFoundError:
        print(f"ERROR: Config file not found: {config_path}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to parse config: {e}")
        sys.exit(1)

    # Extract config values
    paths = cfg["paths"]
    global_ = cfg["global"]
    songs_dir = paths["songs_dir"]
    output_dir = paths["output_dir"]
    ffmpeg_path = paths["ffmpeg_path"]
    speed_ratio = global_["speed_ratio"]
    offset_ratio = global_["offset_ratio"]
    force_lf = global_["force_lf"]

    print(f"\n  Input dir:    {os.path.abspath(songs_dir)}")
    print(f"  Output dir:   {os.path.abspath(output_dir)}")
    print(f"  Speed ratio:  {speed_ratio}x")
    print(f"  Offset ratio: {offset_ratio}")
    print(f"  Force LF:     {force_lf}")
    print()

    if not os.path.isdir(songs_dir):
        print(f"ERROR: Input directory does not exist: {songs_dir}")
        sys.exit(1)

    # ========================================================================
    # 2. Discover song directories
    # ========================================================================
    song_dirs = utils.get_song_dirs(songs_dir)
    if not song_dirs:
        print(f"WARNING: No song subdirectories found under {songs_dir}.")
    else:
        print(f"Found {len(song_dirs)} song director{'y' if len(song_dirs) == 1 else 'ies'}\n")

    # ========================================================================
    # 3. Per-song processing: chart + audio
    # ========================================================================
    aff_total = 0
    aff_success = 0
    audio_success = 0

    for i, song_dir in enumerate(song_dirs, 1):
        song_name = os.path.basename(song_dir)
        print(f"[{i}/{len(song_dirs)}] {song_name}")

        # --- 3a. chart processing ---
        aff_files = utils.collect_files(song_dir, [".aff"])
        aff_config = cfg.get("aff", {})
        excluded_bpm = aff_config.get("excluded_bpm", [])

        for aff_path in aff_files:
            aff_total += 1
            rel = os.path.relpath(aff_path, songs_dir)
            out_path = os.path.join(output_dir, rel)
            if aff_gen.process(
                aff_path, out_path, speed_ratio, offset_ratio,
                excluded_bpm, force_lf,
            ):
                aff_success += 1

        # --- 3b. Audio processing ---
        audio_cfg = cfg.get("audio", {})
        audio_cfg = dict(audio_cfg)  # shallow copy to avoid mutating the original
        audio_cfg["ffmpeg_path"] = ffmpeg_path
        audio_success += audio_gen.process(
            song_dir, output_dir, speed_ratio, audio_cfg,
        )

        print()  # blank line between songs

    # ========================================================================
    # 4. Songlist processing
    # ========================================================================
    print("[songlist]")
    songlist_ok = songlist_gen.process(
        songs_dir, output_dir, speed_ratio, offset_ratio, force_lf,
    )
    print()

    # ========================================================================
    # 5. Copy unprocessed files (images, etc.)
    # ========================================================================
    audio_exts = set(cfg.get("audio", {}).get("include_extensions", [".ogg", ".wav"]))
    skip_exts = {".aff"} | audio_exts
    skip_names = {"songlist"}

    copied = utils.copy_unprocessed(
        songs_dir, output_dir,
        skip_extensions=skip_exts,
        skip_names=skip_names,
    )
    if copied:
        print(f"\nCopied {copied} unprocessed file(s).")

    # ========================================================================
    # 6. Summary
    # ========================================================================
    print("=" * 60)
    print("  Done!")
    print(f"  charts:      {aff_success}/{aff_total} succeeded")
    if songlist_ok:
        print("  Songlist:    processed")
    else:
        print("  Songlist:    not found / skipped")
    print(f"  other:       {copied} copied")
    print("=" * 60)

    _press_enter_to_exit()


def _press_enter_to_exit() -> None:
    """Pause before exiting so the user can see the output (Windows / double-click runs)."""
    if os.name == "nt":
        input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
