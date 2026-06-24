"""Audio generator (FFmpeg-based).

Uses FFmpeg to change audio playback speed. Supports:
- Auto pitch shift (asetrate + aresample)
- Preserve original pitch (atempo cascading)
- Volume adjustment
- Multi-threaded parallel processing
"""

import os
import subprocess
import threading
import json
from concurrent.futures import ThreadPoolExecutor

from . import utils

# All supported audio input extensions
AUDIO_EXTENSIONS = {".wav", ".ogg", ".mp3", ".flac", ".m4a", ".opus", ".aiff", ".aif"}

# Codec lookup table: file extension -> FFmpeg codec name
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
        config: Audio config dict (from config.toml [audio] section).

    Returns:
        Number of files successfully processed.
    """
    global _total_files, _processed_count
    _processed_count = 0

    ffmpeg = _find_ffmpeg()
    force_vorbis = config.get("force_vorbis", True)
    max_workers = config.get("workers", 8)

    # Collect all audio files to process
    tasks = []
    for dirpath, _, filenames in os.walk(songs_dir):
        for f in filenames:
            ext = os.path.splitext(f)[1].lower()
            if ext not in AUDIO_EXTENSIONS:
                continue
            in_file = os.path.join(dirpath, f)
            rel = os.path.relpath(in_file, os.path.dirname(songs_dir))
            if force_vorbis and ext != ".wav":
                out_ext = "ogg"
            else:
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
    codec = _CODEC_MAP.get(ext, "pcm_s16le")

    # Build FFmpeg command
    cmd = [ffmpeg, "-y", "-i", in_file]
    if not config.get("keep_metadata", False):
        cmd.extend(["-map_metadata", "-1"])
    if af:
        cmd.extend(["-af", af])

    cmd.extend(["-c:a", codec])

    # Codec-specific quality / bitrate parameters
    _apply_codec_params(cmd, codec, config)

    # --- Shared output parameters ---
    # Channel count
    channels = config.get("channels", 0)
    if channels > 0:
        cmd.extend(["-ac", str(channels)])

    # Sample rate (0 = keep original)
    samplerate = config.get("samplerate", 0)
    if samplerate != 0:
        cmd.extend(["-ar", str(samplerate)])

    cmd.extend(["-vn", out_file])

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


def _find_ffmpeg() -> str:
    """Return 'ffmpeg' — resolved via system PATH."""
    return "ffmpeg"


def _get_ffprobe(ffmpeg_path: str) -> str:
    """Derive the ffprobe path from the ffmpeg path.

    Handles both Windows (ffmpeg.exe -> ffprobe.exe) and Linux/macOS (ffmpeg -> ffprobe).
    When ffmpeg_path is a bare name like "ffmpeg", returns "ffprobe" (found via PATH).
    """
    if ffmpeg_path.endswith(".exe"):
        return ffmpeg_path.replace("ffmpeg.exe", "ffprobe.exe")
    return ffmpeg_path.replace("ffmpeg", "ffprobe")


def _build_filter(speed: float, sr: int, config: dict) -> str | None:
    """Build the FFmpeg audio filter chain string from config."""
    filters = []
    if config.get("pitch", True):
        filters.append(f"asetrate={sr * speed},aresample={sr}")
    else:
        t = speed
        while t > 2.0:
            filters.append("atempo=2.0")
            t /= 2.0
        while t < 0.5:
            filters.append("atempo=0.5")
            t /= 0.5
        filters.append(f"atempo={t}")

    volume = config.get("volume", 1.0)
    if volume != 1.0:
        filters.append(f"volume={volume}")

    return ",".join(filters) if filters else None


def _apply_codec_params(cmd: list, codec: str, config: dict) -> None:
    """Append codec-specific FFmpeg arguments (bitrate)."""
    if codec == "pcm_s16le":
        return  # lossless — nothing to add

    bitrate = config.get("bitrate", "")
    if bitrate:
        cmd.extend(["-b:a", str(bitrate)])

