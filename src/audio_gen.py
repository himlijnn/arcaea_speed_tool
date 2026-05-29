"""Audio generator (FFmpeg-based).

Uses FFmpeg to change audio playback speed. Supports:
- Auto pitch shift (asetrate + aresample)
- Preserve original pitch (atempo cascading)
- Custom semitone offset
- Volume adjustment
- Metadata handling
- Multi-threaded parallel processing
"""

import os
import subprocess
import threading
import json
from concurrent.futures import ThreadPoolExecutor

from . import utils

# Codec lookup table: file extension → FFmpeg codec name
_CODEC_MAP = {
    ".wav": "pcm_s16le",
    ".mp3": "libmp3lame",
    ".ogg": "libvorbis",
    ".flac": "flac",
    ".m4a": "aac",
    ".opus": "libopus",
}

# Thread-safe progress counters
_progress_lock = threading.Lock()
_processed_count = 0
_total_files = 0


def process(
    songs_dir: str,
    output_dir: str,
    speed_ratio: float,
    config: dict,
) -> int:
    """Process all audio files under the songs directory.

    Args:
        songs_dir: songs input directory.
        output_dir: Output directory.
        speed_ratio: Speed multiplier.
        config: Audio config dict (from config.toml [audio] section, plus ffmpeg_path).

    Returns:
        Number of files successfully processed.
    """
    global _total_files, _processed_count
    _processed_count = 0

    ffmpeg = config["ffmpeg_path"]
    extensions = config.get("include_extensions", [".ogg", ".wav"])
    max_workers = config.get("max_workers", 8)

    # Collect all audio files to process
    tasks = []
    for dirpath, _, filenames in os.walk(songs_dir):
        for f in filenames:
            ext = os.path.splitext(f)[1].lower()
            if ext in extensions:
                in_file = os.path.join(dirpath, f)
                rel = os.path.relpath(in_file, os.path.dirname(songs_dir))
                # Always preserve the original format
                out_ext = ext.lstrip(".")
                out_file = os.path.join(
                    output_dir, f"{os.path.splitext(rel)[0]}.{out_ext}"
                )
                tasks.append((in_file, out_file))

    _total_files = len(tasks)
    if _total_files == 0:
        print("  No audio files found.")
        return 0

    print(f"  Found {_total_files} audio file(s), processing with {max_workers} thread(s)...")

    # Process in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(_process_one, in_f, out_f, speed_ratio, ffmpeg, config)
            for in_f, out_f in tasks
        ]
        success = sum(1 for f in futures if f.result())

    return success


def _process_one(
    in_file: str, out_file: str, speed_ratio: float, ffmpeg: str, config: dict
) -> bool:
    """Process a single audio file with FFmpeg."""
    global _processed_count

    # Get input audio info
    info = _probe(in_file, ffmpeg)
    sr = info.get("sample_rate", 44100)

    # Build audio filter chain
    af = _build_filter(speed_ratio, sr, config)
    utils.ensure_dir(os.path.dirname(out_file))

    # Determine output codec
    ext = os.path.splitext(out_file)[1].lower()
    codec = config.get("audio_codec") or _CODEC_MAP.get(ext, "pcm_s16le")

    # Build FFmpeg command
    cmd = [ffmpeg, "-y", "-i", in_file]
    if not config.get("keep_metadata", True):
        cmd.extend(["-map_metadata", "-1"])
    if af:
        cmd.extend(["-af", af])

    cmd.extend(["-c:a", codec])

    # Quality / bitrate (lossless codecs skip this block)
    if codec not in ("pcm_s16le", "flac"):
        bitrate = config.get("audio_bitrate", "")
        if bitrate:
            cmd.extend(["-b:a", str(bitrate)])
        else:
            quality = int(config.get("audio_quality", 5))
            cmd.extend(_build_quality_args(codec, quality))

    cmd.extend([
        "-ar", str(config.get("audio_samplerate", 44100) or sr),
        "-vn",
        out_file,
    ])

    res = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore"
    )

    with _progress_lock:
        _processed_count += 1
        status = "OK" if res.returncode == 0 else "FAIL"
        print(f"  [{_processed_count}/{_total_files}] {status}: {os.path.basename(in_file)}")

    return res.returncode == 0


def _probe(filepath: str, ffmpeg: str) -> dict:
    """Probe an audio file with ffprobe and return stream info."""
    ffprobe = _get_ffprobe(ffmpeg)
    try:
        result = subprocess.run(
            [ffprobe, "-v", "quiet", "-print_format", "json", "-show_streams", filepath],
            capture_output=True, text=True, encoding="utf-8",
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            for stream in data.get("streams", []):
                if stream.get("codec_type") == "audio":
                    return {"sample_rate": int(stream.get("sample_rate", 44100))}
    except Exception:
        pass
    return {"sample_rate": 44100}


def _get_ffprobe(ffmpeg_path: str) -> str:
    """Derive the ffprobe path from the ffmpeg path.

    Handles both Windows (ffmpeg.exe → ffprobe.exe) and Linux/macOS (ffmpeg → ffprobe).
    When ffmpeg_path is a bare name like "ffmpeg", returns "ffprobe" (found via PATH).
    """
    if ffmpeg_path.endswith(".exe"):
        return ffmpeg_path.replace("ffmpeg.exe", "ffprobe.exe")
    return ffmpeg_path.replace("ffmpeg", "ffprobe")


def _build_filter(speed: float, sr: int, config: dict) -> str | None:
    """Build the FFmpeg audio filter chain string from config."""
    filters = []
    pitch_mode = config.get("pitch_mode", "auto")
    volume = config.get("audio_volume", 1.0)

    if pitch_mode == "auto":
        # Shift pitch naturally with speed: change sample rate then resample
        filters.append(f"asetrate={sr * speed},aresample={sr}")
    elif pitch_mode == "keep":
        # Preserve original pitch using atempo (0.5x–2.0x range; cascade outside)
        t = speed
        while t > 2.0:
            filters.append("atempo=2.0")
            t /= 2.0
        while t < 0.5:
            filters.append("atempo=0.5")
            t /= 0.5
        filters.append(f"atempo={t}")
    elif pitch_mode == "custom":
        if speed != 1.0:
            filters.append(f"atempo={speed}")
        semitones = config.get("custom_pitch_semitones", 0)
        if semitones != 0:
            p = 2 ** (semitones / 12.0)
            filters.append(f"asetrate={sr}*{p},atempo={1 / p},aresample={sr}")

    if volume != 1.0:
        filters.append(f"volume={volume}")

    return ",".join(filters) if filters else None


def _build_quality_args(codec: str, quality: int) -> list[str]:
    """Map a normalized quality value (0-10, higher = better) to codec-specific FFmpeg arguments.

    Different codecs use different scales and directions for -q:a:
      - libvorbis (ogg):  -q:a N     higher = better  (-2..10)
      - libmp3lame (mp3): -q:a 9 - N  lower = better   (0..9, inverted)
      - libopus:           -q:a N     higher = better  (0..10)
    Lossless codecs (pcm_s16le, flac) never reach this function.
    """
    if codec == "libmp3lame":
        # MP3: FFmpeg -q:a 0 = best, 9 = worst → invert
        inverted = max(0, min(9, 9 - quality))
        return ["-q:a", str(inverted)]

    if codec == "aac":
        # AAC: -q:a ~0.1 (worst) to ~2 (best)
        scaled = round(max(0.1, min(2.0, quality / 5.0)), 1)
        return ["-q:a", str(scaled)]

    # libvorbis, libopus: -q:a, higher = better, pass through directly
    return ["-q:a", str(quality)]
