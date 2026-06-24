# Arcaea Speed Tool

Batch speed-change tool for Arcaea songs - charts, audio, and songlist in one time.

[English](README.md) | [简体中文](README_zh_CN.md)

---

### Features

Fast and easy to process the entire songs folder or part of files.

- **Charts** - scales all note time and BPM values by a configurable ratio
  - Includes a BPM exclusion list to prevent some chart play error
- **Audio** - FFmpeg-based multi-threaded audio processing
  - Defaults to 8 worker threads; adjustable based on hardware
  - Pitch options: auto shift or preserve original
  - Accepts all common audio formats; defaults to OGG Vorbis output for non-WAV
- **Songlist** - processes the songlist (json) file
  - Handles BPM strings, base BPM, and audio preview
  - Appends a speed-ratio suffix to localized titles



### Requirements

- Python 3.10+
- [FFmpeg](https://ffmpeg.org) (must be on system PATH)
- [arcfutil](https://pypi.org/project/arcfutil/)

### Quick Start


- Get the source code
```bash
git clone https://github.com/himlijnn/arcaea_speed_tool.git
cd arcaea_speed_tool
pip install .
```
- Install dependencies
```bash
pip install arcfutil
```

- Prepare your songs folder, example structure:
```
    songs/
        particlearts/
            0.aff, 1.aff, 2.aff, ...
            base.ogg
            ...
        songlist
```
- Run from command line, or double-click run.py
```bash
arcaea-speed-tool
```

### Examples
- Full: 1.25x speed, custom I/O, keep original pitch
```bash
arcaea-speed-tool -i ./songs -o ./my_output -s 1.25 -np
```
- Charts only, custom config, no file copy
```bash
arcaea-speed-tool -m chart -nc -s 1.25 --config my_config.toml
```
- 2x speed, auto pitch shift, higher bitrate
```bash
arcaea-speed-tool -s 2 -p --bitrate 256k
```

### Command Reference

All settings can be specified via CLI arguments. If omitted (or when running run.py directly), values are read from config.toml. CLI arguments take precedence over config file values.

| Argument | Description | Default |
|-|-|-|
| `-i, --input-dir PATH` | Input directory | |
| `-o, --output-dir PATH` | Output directory | |
| `-s, --speed FLOAT` | Speed multiplier | |
| `-m, --mode MODE` | all / chart / audio / songlist | all |
| `-c, --copy` / `-nc, --no-copy` | Copy unprocessed files to output | true |
| `-p, --pitch` / `-np, --no-pitch` | Auto pitch shift with speed | true |
| `-e, --enable-exclusion` / `-ne, --no-exclusion` | Use BPM exclusion list | true |
| `-w, --workers N` | Parallel worker threads for audio | |
| `--offset FLOAT` | Audio offset ratio | |
| `--force-lf` / `--no-force-lf` | Force LF line endings | true |
| `--force-vorbis` / `--no-force-vorbis` | Convert non-WAV to OGG Vorbis | true |
| `--keep-metadata` / `--no-keep-metadata` | Keep audio metadata tags | false |
| `--channels N` | Output channel count | |
| `--volume FLOAT` | Volume multiplier | |
| `--bitrate STR` | Audio bitrate | |
| `--samplerate N` | Output sample rate | |
| `--config PATH` | Custom config file path | |

See [config.toml](config.toml) for all options.


### Acknowledgments

- [arcfutil](https://github.com/feightwywx/arcfutil) - Arcaea File Utility
- 黎明职业中学 - developer (confidential)
