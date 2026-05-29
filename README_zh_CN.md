# Arcaea Speed Tool

*Arcaea 曲目批量变速工具 - 支持谱面、音频、songlist 一次性处理。*

[English](README.md) | [简体中文](README_zh_CN.md)

---

### 功能

- **谱面变速** - 按指定倍率缩放所有音符时间与 BPM 值，内置排除列表以修复一些谱面演出错误
- **音频变速** - 基于 FFmpeg 的多线程处理，支持多种音高模式（自动升降调 / 保持原调 / 自定义半音）
- **Songlist 变速** - 缩放 BPM 字符串、基准 BPM、音频预览，并为多语言标题追加变速倍率后缀
- **跨平台** - 支持 Windows、Linux、macOS（需安装 FFmpeg）


### 环境依赖

- Python 3.10+
- FFmpeg
- [arcfutil](https://pypi.org/project/arcfutil/)

### 快速开始

```bash
# 1. 克隆并安装
git clone https://github.com/himlijnn/arcaea_speed_tool.git
cd arcaea_speed_tool
pip install .

# 2. 准备 songs 文件夹
#    songs/
#      <曲目名称>/
#        0.aff, 1.aff, ...
#        base.ogg
#      songlist

# 3. 编辑 config.toml - 设置变速倍率、FFmpeg 路径等

# 4. 运行
arcaea-speed-tool
# 或: python -m src.main
```

### 配置说明

在工作目录下编辑 **config.toml**：

```toml
[paths]
songs_dir = "./songs"
output_dir = "./songs_output"
ffmpeg_path = "ffmpeg"        # Linux/macOS 用 "ffmpeg"，Windows 填写完整路径

[global]
speed_ratio = 1.25             # 核心变速倍率
offset_ratio = 0.8             # AudioOffset / audioPreview 缩放（通常为 1/speed_ratio）为保证精度，将变速倍率与其倒数分开配置
force_lf = true                # 强制 LF 换行
```

完整选项详见 [config.toml](config.toml)。



### 项目结构

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

### 协议

[MIT](LICENSE)

### 致谢

- [arcfutil](https://github.com/feightwywx/arcfutil) - Arcaea File Utility
- 早期逐个谱面排查兼容性的所有成员
- 黎明职业中学（开发者，身份保密）

### 作者

**[him lijnn](https://github.com/himlijnn)**
