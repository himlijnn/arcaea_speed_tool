# Arcaea Speed Tool

*Speed-change tool for Arcaea songs - charts, audio, and songlist.*

[English](README.md) | [简体中文](README_zh_CN.md)

---

### Features

- **Charts** - scales all note timestamps and BPM values by a configurable ratio, with a built-in exclusion list for per-chart compatibility fixes
- **Audio** - FFmpeg-based multi-threaded speed change with multiple pitch modes (auto shift / preserve pitch / custom semitone)
- **Songlist** - scales BPM strings, BPM base, audio preview, and appends a speed-ratio suffix to localized titles
- **Cross-platform** - works on Windows, Linux, and macOS (FFmpeg required)

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

# 2. Prepare your songs folder
#    songs/
#      <song_name>/
#        0.aff, 1.aff, ...
#        base.ogg
#      songlist

# 3. Edit config.toml - set speed_ratio, ffmpeg_path, etc.

# 4. Run
arcaea-speed-tool
# or: python -m src.main
```

### Configuration

Edit **config.toml** in your working directory:

```toml
[paths]
songs_dir = "./songs"
output_dir = "./songs_output"
ffmpeg_path = "ffmpeg"        # "ffmpeg" on Linux/macOS, full path on Windows

[global]
speed_ratio = 1.25             # speed multiplier
offset_ratio = 0.8             # AudioOffset / audioPreview scale (inverse of speed_ratio, kept separate for precision)
force_lf = true                # enforce LF line endings
```

See [config.toml](config.toml) for all options.


### Project Structure

```
arcaea_speed_tool/
├── src/
│   ├── __init__.py
│   ├── config.py              # config.toml loader
│   ├── utils.py               # shared utilities
│   ├── aff_gen.py             # chart generator
│   ├── songlist_gen.py        # songlist generator
│   ├── audio_gen.py           # audio generator (FFmpeg)
│   ├── main.py                # main entry point
│   └── crlf2lf.py             # standalone CRLF→LF converter
├── config.toml
├── pyproject.toml
├── LICENSE                    # MIT
└── requirements.txt
```

### License

[MIT](LICENSE)

### Acknowledgments

- [arcfutil](https://github.com/feightwywx/arcfutil) - Arcaea File Utility
- All members who helped with per-chart compatibility testing
- 黎明职业中学 (developer, identity keep secret)

### Author

**[him lijnn](https://github.com/himlijnn)**
