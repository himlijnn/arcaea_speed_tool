"""Arcaea Speed Tool — main entry point.

Processes the entire songs folder structure:
  songs/
    <song_name>/
      0.aff, 1.aff, ...   -> chart speed change
      base.ogg            -> audio speed change
    songlist              -> songlist speed change

All output is written to output_dir, preserving the original directory structure.
"""

import argparse
import os
import sys

from . import utils
from .config import load_config
from . import aff_gen
from . import songlist_gen
from . import audio_gen


def main() -> None:
    """Run the full processing pipeline."""
    parser = _build_parser()
    args = parser.parse_args()

    # ========================================================================
    # 1. Load configuration
    # ========================================================================
    try:
        cfg = load_config(args.config)
    except FileNotFoundError:
        print(f"ERROR: Config file not found: {args.config}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to parse config: {e}")
        sys.exit(1)

    # ========================================================================
    # 2. Merge CLI args with config (CLI overrides config)
    # ========================================================================
    paths = cfg["paths"]
    global_ = cfg["global"]

    input_dir = args.input_dir or paths["input_dir"]
    output_dir = args.output_dir or paths["output_dir"]
    speed_ratio = args.speed if args.speed is not None else global_["speed"]
    offset_ratio = args.offset if args.offset is not None else global_.get("offset", 0)
    if offset_ratio == 0:
        offset_ratio = 1.0 / speed_ratio
    mode = (args.mode or global_.get("mode", "all")).strip().lower()
    force_lf = args.force_lf if args.force_lf is not None else global_.get("force_lf", True)
    copy_unprocessed = args.copy if args.copy is not None else global_.get("copy", True)

    run_chart = mode in ("all", "chart")
    run_audio = mode in ("all", "audio")
    run_songlist = mode in ("all", "songlist")
    run_all = mode == "all"

    # Audio overrides
    audio_cfg = cfg.get("audio", {})
    audio_cfg = dict(audio_cfg)
    if args.pitch is not None:
        audio_cfg["pitch"] = args.pitch
    if args.channels is not None:
        audio_cfg["channels"] = args.channels
    if args.volume is not None:
        audio_cfg["volume"] = args.volume
    if args.bitrate is not None:
        audio_cfg["bitrate"] = args.bitrate
    if args.samplerate is not None:
        audio_cfg["samplerate"] = args.samplerate
    if args.force_vorbis is not None:
        audio_cfg["force_vorbis"] = args.force_vorbis
    if args.keep_metadata is not None:
        audio_cfg["keep_metadata"] = args.keep_metadata
    if args.workers is not None:
        audio_cfg["workers"] = args.workers

    # Aff overrides
    aff_cfg = cfg.get("aff", {})
    aff_cfg = dict(aff_cfg)
    if args.enable_exclusion is not None:
        aff_cfg["enable_exclusion"] = args.enable_exclusion

    # ========================================================================
    # 3. Print summary
    # ========================================================================
    print("=" * 60)
    print("  Arcaea Speed Tool — chart / audio / songlist")
    print("=" * 60)
    print(f"\n  Input dir:    {os.path.abspath(input_dir)}")
    print(f"  Output dir:   {os.path.abspath(output_dir)}")
    print(f"  Speed ratio:  {speed_ratio}x")
    print(f"  Offset ratio: {offset_ratio}{' (auto)' if offset_ratio == 1.0 / speed_ratio else ''}")
    print(f"  Mode:         {'all' if mode == '' else mode}")
    print(f"  Force LF:     {force_lf}")
    print()

    if not os.path.isdir(input_dir):
        print(f"ERROR: Input directory does not exist: {input_dir}")
        sys.exit(1)

    # ========================================================================
    # 4. Discover song directories
    # ========================================================================
    song_dirs = utils.get_song_dirs(input_dir)
    if not song_dirs:
        print(f"WARNING: No song subdirectories found under {input_dir}.")
    else:
        print(f"Found {len(song_dirs)} song director{'y' if len(song_dirs) == 1 else 'ies'}\n")

    # ========================================================================
    # 5. Per-song processing: chart + audio
    # ========================================================================
    aff_total = 0
    aff_success = 0
    audio_success = 0

    for i, song_dir in enumerate(song_dirs, 1):
        song_name = os.path.basename(song_dir)
        print(f"[{i}/{len(song_dirs)}] {song_name}")

        # --- 5a. chart processing ---
        if run_chart:
            aff_files = utils.collect_files(song_dir, [".aff"])
            if aff_cfg.get("enable_exclusion", True):
                excluded_bpm = aff_cfg.get("excluded_bpm", [])
            else:
                excluded_bpm = []

            for aff_path in aff_files:
                aff_total += 1
                rel = os.path.relpath(aff_path, input_dir)
                out_path = os.path.join(output_dir, rel)
                if aff_gen.process(
                    aff_path, out_path, speed_ratio, offset_ratio,
                    excluded_bpm, force_lf,
                ):
                    aff_success += 1
        else:
            print("  (chart skipped)")

        # --- 5b. Audio processing ---
        if run_audio:
            audio_success += audio_gen.process(
                song_dir, output_dir, speed_ratio, audio_cfg,
            )
        else:
            print("  (audio skipped)")

        print()

    # ========================================================================
    # 6. Songlist processing
    # ========================================================================
    if run_songlist:
        print("[songlist]")
        songlist_ok = songlist_gen.process(
            input_dir, output_dir, speed_ratio, offset_ratio, force_lf,
        )
        print()
    else:
        print("[songlist] (skipped)\n")
        songlist_ok = False

    # ========================================================================
    # 7. Copy unprocessed files (images, etc.)
    # ========================================================================
    copied = 0
    if run_all and copy_unprocessed:
        skip_exts = {".aff"} | audio_gen.AUDIO_EXTENSIONS
        skip_names = {"songlist"}

        copied = utils.copy_unprocessed(
            input_dir, output_dir,
            skip_extensions=skip_exts,
            skip_names=skip_names,
        )
        if copied:
            print(f"Copied {copied} unprocessed file(s).\n")

    # ========================================================================
    # 8. Summary
    # ========================================================================
    print("=" * 60)
    print("  Done!")
    if run_chart:
        print(f"  charts:      {aff_success}/{aff_total} succeeded")
    if run_songlist:
        if songlist_ok:
            print("  Songlist:    processed")
        else:
            print("  Songlist:    not found")
    print(f"  other:       {copied} copied")
    print("=" * 60)

    _press_enter_to_exit()


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    p = argparse.ArgumentParser(
        prog="arcaea-speed-tool",
        description="Arcaea Speed Tool — batch speed-change for charts, audio, and songlist.",
    )

    # ---- Config ----
    p.add_argument("--config", default="config.toml",
                   help="Path to config.toml (default: config.toml)")

    # ---- Paths ----
    p.add_argument("-i", "--input-dir", default=None,
                   help="Input songs directory")
    p.add_argument("-o", "--output-dir", default=None,
                   help="Output directory")

    # ---- Global ----
    p.add_argument("-s", "--speed", type=float, default=None,
                   help="Speed multiplier (e.g. 1.25)")
    p.add_argument("--offset", type=float, default=None,
                   help="Audio offset ratio (0 = auto: 1/speed)")
    p.add_argument("-m", "--mode", default=None,
                   choices=["all", "chart", "audio", "songlist"],
                   help="Processing mode (default: all)")
    p.add_argument("-c", "--copy", action="store_true", default=None,
                   help="Copy unprocessed files to output")
    p.add_argument("-nc", "--no-copy", action="store_false", dest="copy", default=None,
                   help="Do not copy unprocessed files")
    p.add_argument("--force-lf", action="store_true", default=None,
                   help="Force LF line endings on output")
    p.add_argument("--no-force-lf", action="store_false", dest="force_lf", default=None,
                   help="Disable forced LF line endings")

    # ---- Audio ----
    g_audio = p.add_argument_group("audio options")
    g_audio.add_argument("-p", "--pitch", action="store_true", default=None,
                         help="Shift pitch with speed (default: on)")
    g_audio.add_argument("-np", "--no-pitch", action="store_false", dest="pitch", default=None,
                         help="Preserve original pitch")
    g_audio.add_argument("-w", "--workers", type=int, default=None,
                         help="Number of parallel worker threads (default: 8)")
    g_audio.add_argument("--channels", type=int, default=None,
                         help="Output channel count (1=mono, 2=stereo)")
    g_audio.add_argument("--volume", type=float, default=None,
                         help="Volume multiplier (1=unchanged)")
    g_audio.add_argument("--bitrate", default=None,
                         help="Audio bitrate (e.g. '188k')")
    g_audio.add_argument("--samplerate", type=int, default=None,
                         help="Output sample rate in Hz (0=keep original)")
    g_audio.add_argument("--force-vorbis", action="store_true", default=None,
                         help="Force non-WAV to OGG Vorbis output (default: on)")
    g_audio.add_argument("--no-force-vorbis", action="store_false", dest="force_vorbis", default=None,
                         help="Keep original encoding")
    g_audio.add_argument("--keep-metadata", action="store_true", default=None,
                         help="Keep audio metadata tags")
    g_audio.add_argument("--no-keep-metadata", action="store_false", dest="keep_metadata", default=None,
                         help="Strip audio metadata (default)")

    # ---- Aff ----
    g_aff = p.add_argument_group("chart options")
    g_aff.add_argument("-e", "--enable-exclusion", action="store_true", default=None,
                       help="Enable BPM exclusion list (default: on)")
    g_aff.add_argument("-ne", "--no-exclusion", action="store_false", dest="enable_exclusion", default=None,
                       help="Disable BPM exclusion list")

    return p


def _press_enter_to_exit() -> None:
    if os.name == "nt":
        input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
