# Arcaea Speed Tool

*Batch speed-change tool for Arcaea songs - charts, audio, and songlist in one time.*

[English](README.md) | [简体中文](README_zh_CN.md)

---

### Features

One-click speed processing for the entire **songs** folder!

- **Charts** - scales all note time and BPM values by a configurable ratio
  - Includes a BPM exclusion list to prevent chart play error
- **Audio** - FFmpeg-based multi-threaded audio processing
  - Defaults to 8 worker threads; adjustable based on hardware
  - Pitch mode options: auto shift, preserve original, or manual
  - Processes ogg and wav files by default
- **Songlist** - processes the songlist (json) file
  - Handles BPM strings, base BPM, and audio preview
  - Appends a speed-ratio suffix to localized titles



### Requirements

- Python 3.10+
- FFmpeg
- [arcfutil](https://pypi.org/project/arcfutil/)

### Quick Start

```bash
# 1. Clone and install
git clone https://github.com/himlijnn/arcaea_speed_tool.git
cd arcaea_speed_tool
pip install .
# or: download source code manually

# 2. Install dependencies
pip install arcfutil

# 3. Prepare your songs folder
#    songs/
#      <song_name>/
#        0.aff, 1.aff, ...
#        base.ogg
#      songlist

# 4. Edit config.toml — set speed ratio, paths, etc.

# 5. Run
arcaea-speed-tool
# or: run run.py
```

### Configuration

Edit the key options in **config.toml** under your working directory:

```toml
[paths]
songs_dir = "./songs"
output_dir = "./songs_output"
ffmpeg_path = "ffmpeg"
# Use "ffmpeg" on Linux/macOS; full path on Windows

[global]
speed_ratio = 1.25             # speed multiplier
offset_ratio = 0.8             # AudioOffset scale
# Kept separate from speed_ratio for precision
force_lf = true                # enforce LF line endings

# ...
```

See [config.toml](config.toml) for all options.


### Acknowledgments

- [arcfutil](https://github.com/feightwywx/arcfutil) — Arcaea File Utility
- 黎明职业中学 — developer (confidential)

