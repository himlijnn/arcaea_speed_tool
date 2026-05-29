"""Songlist generator.

Processes the songlist file (JSON format):
1. Scale BPM strings and bpm_base values
2. Scale audioPreview / audioPreviewEnd timestamps
3. Append a speed-ratio suffix to title_localized
"""

import json
import math
import os
import re

from . import utils

# The songlist filename is always "songlist" (no extension)
_SONGLIST_FILENAME = "songlist"


def process(
    songs_dir: str,
    output_dir: str,
    speed_ratio: float,
    offset_ratio: float,
    force_lf: bool = True,
) -> bool:
    """Process the songlist file: locate, transform, write.

    Args:
        songs_dir: songs input directory.
        output_dir: Output directory.
        speed_ratio: Speed multiplier.
        offset_ratio: audioPreview scaling ratio.
        force_lf: Whether to enforce LF line endings.

    Returns:
        True if processing succeeded.
    """
    input_file = os.path.join(songs_dir, _SONGLIST_FILENAME)
    if not os.path.isfile(input_file):
        print(f"  WARNING: songlist file not found: {input_file}")
        return False

    output_file = os.path.join(output_dir, _SONGLIST_FILENAME)

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        _process_json(data, speed_ratio, offset_ratio)

        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        utils.write_text_lf(output_file, json_str, force_lf)
        return True

    except Exception as e:
        print(f"  ERROR: Failed to process songlist: {e}")
        return False


# ============================================================================
# Internal helpers
# ============================================================================


def _process_json(obj, speed_ratio: float, offset_ratio: float) -> None:
    """Recursively walk a JSON object and apply speed transformations to specific fields."""
    if isinstance(obj, dict):
        # Scale numbers inside BPM strings
        if "bpm" in obj and isinstance(obj["bpm"], str):
            obj["bpm"] = _scale_bpm_string(obj["bpm"], speed_ratio)

        # Scale bpm_base numeric value
        if "bpm_base" in obj and isinstance(obj["bpm_base"], (int, float)):
            obj["bpm_base"] = utils.format_number(obj["bpm_base"] * speed_ratio)

        # Scale audio preview times
        if "audioPreview" in obj and isinstance(obj["audioPreview"], (int, float)):
            obj["audioPreview"] = math.floor(obj["audioPreview"] * offset_ratio)

        if "audioPreviewEnd" in obj and isinstance(obj["audioPreviewEnd"], (int, float)):
            obj["audioPreviewEnd"] = math.floor(obj["audioPreviewEnd"] * offset_ratio)

        # Append speed-ratio suffix to localized titles
        if "title_localized" in obj and isinstance(obj["title_localized"], dict):
            obj["title_localized"] = _add_title_suffix(
                obj["title_localized"], speed_ratio
            )

        for value in obj.values():
            _process_json(value, speed_ratio, offset_ratio)

    elif isinstance(obj, list):
        for item in obj:
            _process_json(item, speed_ratio, offset_ratio)


def _scale_bpm_string(bpm_str: str, speed_ratio: float) -> str:
    """Scale all numeric values inside a BPM string.

    Example: "100-200" * 1.25 → "125.0-250.0"
    """
    numbers = re.findall(r"\d+\.?\d*", bpm_str)
    if not numbers:
        return bpm_str

    scaled = [str(utils.format_number(float(n) * speed_ratio)) for n in numbers]
    return re.sub(r"\d+\.?\d*", lambda _: scaled.pop(0), bpm_str)


def _add_title_suffix(title_localized: dict, speed_ratio: float) -> dict:
    """Append a speed-ratio suffix to each language's title in title_localized."""
    suffix = f" {speed_ratio}"
    for lang, title in title_localized.items():
        if isinstance(title, str):
            title_localized[lang] = title + suffix
        elif isinstance(title, list):
            title_localized[lang] = [
                item + suffix if isinstance(item, str) else item for item in title
            ]
    return title_localized
