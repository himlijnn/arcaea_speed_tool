# Arcaea Speed Tool

Arcaea 曲目批量变速工具 - 支持谱面、音频、songlist 一键处理。

[English](README.md) | [简体中文](README_zh_CN.md)

---

### 功能

轻松对整个 songs 文件夹或部分文件变速处理！
- **谱面变速** - 按指定倍率缩放所有 note 时间与 BPM 值
  - 内置人工整理的 BPM 排除列表，防止一些谱面播放错误
- **音频变速** - 基于 FFmpeg 的多线程音频处理
  - 默认 8 线程处理，可根据设备性能手动调整
  - 可选择自动变调或保持原音调
  - 支持全部常见音频格式；默认将非 WAV 文件转为 OGG Vorbis 输出
- **Songlist 变速** - 处理 songlist（json）文件
  - 灵活处理 BPM 字符串、基准 BPM、音频预览
  - 多语言标题追加变速倍率后缀



### 环境依赖

- Python 3.10+
- [FFmpeg](https://ffmpeg.org)（需加入 PATH 环境变量）
- [arcfutil](https://pypi.org/project/arcfutil/)

### 快速开始


- 获取或手动下载源代码
```bash
git clone https://github.com/himlijnn/arcaea_speed_tool.git
cd arcaea_speed_tool
pip install .
```
- 准备依赖
```bash
pip install arcfutil
```

- 准备 songs 文件夹，示例如下
```
    songs/
        particlearts/
            0.aff, 1.aff, 2.aff, ...
            base.ogg
            ...
        songlist
```
- 在命令行运行，或手动运行 run.py
```bash
arcaea-speed-tool
```

### 使用示例
- 全流程：1.25 倍速，指定输入输出路径，保持原调
```bash
arcaea-speed-tool -i ./songs -o ./my_output -s 1.25 -np
```
- 1.25 倍速，仅处理谱面，并指定配置文件
```bash
arcaea-speed-tool -m chart -nc -s 1.25 --config my_config.toml
```
- 2 倍速，自动变调，更高的比特率
```bash
arcaea-speed-tool -s 2 -p --bitrate 256k
```

### 命令参考

所有设置均可使用命令行参数。若参数留空，或手动运行 run.py，则读取 config.toml 中的选项。命令行参数优先级高于配置文件。

| 参数 | 说明 | 默认值 |
|-|-|-|
| `-i, --input-dir PATH` | 输入目录 | |
| `-o, --output-dir PATH` | 输出目录 | |
| `-s, --speed FLOAT` | 变速倍率 | |
| `-m, --mode MODE` | 模式 all / chart / audio / songlist | all |
| `-c, --copy` / `-nc, --no-copy` | 复制未处理文件到输出目录 | true |
| `-p, --pitch` / `-np, --no-pitch` | 音频变调 | true |
| `-e, --enable-exclusion` / `-ne, --no-exclusion` | 使用 BPM 排除列表 | true |
| `-v, --force-vorbis` / `-nv, --no-force-vorbis` | 强制非 WAV 音频转为 OGG Vorbis | true |
| `-w, --workers N` | 音频处理并行线程数 | |
| `--offset FLOAT` | 音频 offset 倍率 | |
| `--force-lf` / `--no-force-lf` | 强制 LF 换行符 | true |
| `--keep-metadata` / `--no-keep-metadata` | 保留音频元数据 | false |
| `--channels N` | 输出声道数 | |
| `--volume FLOAT` | 音量倍率 | |
| `--bitrate STR` | 音频比特率 | |
| `--samplerate N` | 输出采样率 | |
| `--config PATH` | 自定义配置文件路径 | |

更多内容详见 [config.toml](config.toml)。

### 致谢

- [arcfutil](https://github.com/feightwywx/arcfutil) - Arcaea File Utility
- 黎明职业中学 - 开发者（保密）
