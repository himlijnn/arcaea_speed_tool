"""Chart generator.

Pipeline:
1. Text layer: scale AudioOffset
2. Parse into objects via arcfutil.aff
3. Time scaling: scale_group() scales all timestamps by speed_ratio and rounds
4. Filtering: filter_by_standard() removes negative-time events
5. Text fix: fix_timing_tap_conflict() resolves timing-vs-tap time conflicts
6. Write: optionally enforce LF line endings
"""

import traceback
from decimal import Decimal

from arcfutil import aff

from . import utils


def process(
    input_file: str,
    output_file: str,
    speed_ratio: float,
    offset_ratio: float,
    excluded_bpm: list[float],
    force_lf: bool = True,
) -> bool:
    """Process a single .aff file: speed change + time offset + filter + line-ending fix.

    Args:
        input_file: Path to the input .aff file.
        output_file: Path to the output .aff file.
        speed_ratio: Speed multiplier.
        offset_ratio: AudioOffset scaling ratio.
        excluded_bpm: List of BPM values to exclude from scaling.
        force_lf: Whether to enforce LF line endings.

    Returns:
        True if processing succeeded.
    """
    try:
        # 1. Read raw text
        with open(input_file, "r", encoding="utf-8") as f:
            chart_str = f.read()

        # 2. Text layer: scale AudioOffset (before parsing, since it is not an AffNote)
        chart_str = _scale_audio_offset(chart_str, offset_ratio)

        # 3. Parse into AffNote list
        chart = aff.load(chart_str)

        # 4. Core: time scaling + BPM scaling
        scaled = _scale_group(chart, speed_ratio, excluded_bpm)

        # 5. Filter: remove negative-time events
        filtered = _filter_by_standard(scaled)

        # 6. Serialize back to text
        result_str = filtered.__str__()

        # 7. Text fix: timing-tap time conflict
        result_str = _fix_timing_tap_conflict(result_str)

        # 8. Write output
        utils.write_text_lf(output_file, result_str, force_lf)
        return True

    except Exception:
        print(f"  ERROR: Failed to process {input_file}: {traceback.format_exc()}")
        return False


# ============================================================================
# Internal helpers
# ============================================================================


def _scale_audio_offset(content: str, offset_ratio: float) -> str:
    """Scale the AudioOffset line (text-level operation, runs before aff.load)."""
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("AudioOffset:"):
            try:
                original = int(line.split(":")[1].strip())
                lines[i] = f"AudioOffset:{int(original * offset_ratio)}"
                break
            except ValueError:
                pass
    return "\n".join(lines)


def _scale_group(notes: list, scale_factor: float, excluded_bpm: list[float]) -> list:
    """Scale all time-based objects in the chart.

    Algorithm:
    1. Collect all objects with time attributes (Timing, Tap, Hold, Arc, etc.)
    2. Compute exact scaled time = original_time / scale_factor
    3. Sort by original time, round to integers, ensure monotonic non-decreasing order
    4. Write the mapped times back to objects
    5. Scale BPM values (except those in the exclusion list)
    6. Handle Arc skynote time arrays
    """
    time_objects = _collect_time_objects(notes, scale_factor)
    time_objects.sort(key=lambda x: x["orig_time"])
    time_mapping = _build_time_mapping(time_objects)
    _apply_time_mapping(notes, time_mapping, scale_factor, excluded_bpm)
    _fix_simultaneous_events(notes)
    return notes


def _collect_time_objects(group: list, scale_factor: float) -> list:
    """Recursively collect all objects with time attributes and compute exact scaled times."""
    result = []

    def exact_time(t):
        d_orig = Decimal(str(t))
        d_factor = Decimal(str(scale_factor))
        return float(d_orig / d_factor)

    def walk(items):
        for item in items:
            if item is None:
                continue
            if isinstance(item, aff.NoteGroup):
                walk(item)
            elif isinstance(item, aff.Timing):
                result.append({
                    "type": "timing",
                    "obj": item,
                    "orig_time": item.time,
                    "exact_time": exact_time(item.time),
                })
            elif hasattr(item, "time"):
                obj_type = type(item).__name__
                result.append({
                    "type": obj_type,
                    "obj": item,
                    "orig_time": item.time,
                    "exact_time": exact_time(item.time),
                })
                # Objects with duration (Hold, Arc) — also collect end time
                if hasattr(item, "totime"):
                    result.append({
                        "type": f"{obj_type}_end",
                        "obj": item,
                        "orig_time": item.totime,
                        "exact_time": exact_time(item.totime),
                        "parent_obj": item,
                    })

    walk(group)
    return result


def _build_time_mapping(time_objects: list) -> dict:
    """Build a mapping from original time -> scaled rounded time.

    Rule: round-half-up, and ensure mapped times are strictly non-decreasing
    (each subsequent time >= previous + 1).
    """
    time_mapping = {}
    last_rounded = -1

    for obj in time_objects:
        orig = obj["orig_time"]
        if orig in time_mapping:
            continue

        rounded = utils.to_int_round_half_up(obj["exact_time"])
        if rounded <= last_rounded:
            rounded = last_rounded + 1
        time_mapping[orig] = rounded
        last_rounded = rounded

    return time_mapping


def _apply_time_mapping(
    group: list,
    time_mapping: dict,
    scale_factor: float,
    excluded_bpm: list[float],
) -> None:
    """Write the time mapping back onto all objects, and scale BPM values."""

    def walk(items):
        for item in items:
            if item is None:
                continue
            if isinstance(item, aff.NoteGroup):
                walk(item)
                continue

            # Update time
            if hasattr(item, "time") and item.time in time_mapping:
                item.time = time_mapping[item.time]

            # Scale BPM (unless excluded)
            if isinstance(item, aff.Timing):
                if item.bpm not in excluded_bpm:
                    item.bpm *= scale_factor

            # Update totime (end time for Hold / Arc)
            if hasattr(item, "totime") and item.totime in time_mapping:
                item.totime = time_mapping[item.totime]
                if item.totime < item.time:
                    item.totime = item.time

            # Arc skynote time array
            if isinstance(item, aff.Arc) and item.skynote is not None:
                item.skynote = [
                    time_mapping.get(t, utils.to_int_round_half_up(
                        float(Decimal(str(t)) / Decimal(str(scale_factor)))
                    ))
                    for t in item.skynote
                    if t is not None
                ]

    walk(group)


def _fix_simultaneous_events(notes: list) -> None:
    """Detect and report Timing-vs-other-event conflicts at the same time point.

    Note: the current version only collects data; actual timing adjustment is
    reserved as an extension point.
    """
    time_events = {}

    def collect(g):
        for item in g:
            if item is None:
                continue
            if isinstance(item, aff.NoteGroup):
                collect(item)
                continue
            if hasattr(item, "time"):
                t = item.time
                if t not in time_events:
                    time_events[t] = set()
                time_events[t].add(type(item).__name__)

    collect(notes)

    for _time_val, _event_types in time_events.items():
        if "Timing" in _event_types and len(_event_types) > 1:
            pass  # Reserved for future adjustments


def _filter_by_standard(notes: list) -> list:
    """Filter out negative-time events (except Timing at time=0).

    Also cleans up empty TimingGroups.
    """

    def walk(group):
        for i, item in enumerate(group):
            if isinstance(item, aff.NoteGroup):
                walk(item)
                if isinstance(item, aff.TimingGroup):
                    filtered = aff.TimingGroup(
                        list(filter(lambda x: x is not None, item)), opt=item.option
                    )
                    group[i] = filtered if len(filtered) > 0 else None
            else:
                # Remove negative-time events (except Timing at time=0)
                if item.time < 0 and not (item.time == 0 and isinstance(item, aff.Timing)):
                    group[i] = None
        return group

    return walk(notes)


def _fix_timing_tap_conflict(content: str) -> str:
    """Fix timing vs. tap time conflicts.

    After scaling, a tap's time may end up earlier than its preceding timing event,
    which is invalid in Arcaea. Fix: clamp the tap's time to the last timing time.
    """
    lines = content.split("\n")
    result = []
    last_timing_time = None

    for line in lines:
        stripped = line.strip()

        # Detect timing(...) lines and record their time
        if stripped.startswith("timing(") and stripped.endswith(");"):
            try:
                time_str = stripped[7:-2].split(",")[0]
                last_timing_time = int(time_str)
                result.append(line)
                continue
            except (ValueError, IndexError):
                last_timing_time = None
                result.append(line)
                continue

        # Detect tap(...) lines (not hold, not arc, no [] i.e. not Camera)
        if (
            last_timing_time is not None
            and stripped.startswith("(")
            and stripped.endswith(");")
            and "," in stripped
            and not stripped.startswith("(hold")
            and not stripped.startswith("(arc")
            and "[" not in stripped
        ):
            try:
                tap_time = int(stripped[1:-2].split(",")[0])
                if tap_time < last_timing_time:
                    comma_pos = stripped.find(",")
                    result.append(f"({last_timing_time}{stripped[comma_pos:]}")
                else:
                    result.append(line)
            except (ValueError, IndexError):
                result.append(line)
        else:
            # Not a tap that follows a timing — reset
            last_timing_time = None
            result.append(line)

    return "\n".join(lines)
