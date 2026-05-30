# Arcaea Speed Tool

*Arcaea 曲目批量变速工具 - 支持谱面、音频、songlist 一键处理。*

[English](README.md) | [简体中文](README_zh_CN.md)

---

### 功能
一键对整个 **songs** 文件夹变速处理！
- **谱面变速** - 按指定倍率缩放所有 note 时间与 BPM 值
  - 内置人工整理的 BPM 排除列表，防止出现谱面演出错误
- **音频变速** - 基于 FFmpeg 的多线程音频处理
  - 默认 8 线程处理，可根据设备性能手动调整
  - 可选择自动变调、保持原音调或手动指定
  - 默认处理 ogg 与 wav 格式文件
- **Songlist 变速** - 处理 songlist（json）文件
  - 灵活处理 BPM 字符串、基准 BPM、音频预览
  - 多语言标题追加变速倍率后缀



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
# 或: 手动下载源代码

# 2. 准备依赖
pip install arcfutil

# 3. 准备 songs 文件夹
#    songs/
#      <song_name>/
#        0.aff, 1.aff, ...
#        base.ogg
#      songlist

# 4. 编辑 config.toml - 设置变速倍率、路径等

# 5. 运行
arcaea-speed-tool
# 或: 运行 run.py
```

### 配置说明

在工作目录下编辑 **config.toml** 中的重要选项：

```toml
[paths]
songs_dir = "./songs"
output_dir = "./songs_output"
ffmpeg_path = "ffmpeg"
# Linux/macOS 填写 "ffmpeg"，Windows 填写完整路径

[global]
speed_ratio = 1.25             # 变速倍率

# ...
```

完整选项详见 [config.toml](config.toml)。


### 致谢

- [arcfutil](https://github.com/feightwywx/arcfutil) - Arcaea File Utility
- 黎明职业中学 - 开发者（保密）

