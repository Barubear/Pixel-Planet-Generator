# 🌍 Pixel Planet Generator

一个使用 Python 与 Pillow 编写的程序化像素风星球、银河背景与帧动画生成器。

## ✨ 功能

- 多种星球调色板：earth、desert、lava、toxic、ice、ocean、alien、forest、gas、mono
- 可复现的种子生成
- 可选土星环、四角像素边框与灰度/紫色后处理
- 星球自转动画帧序列（15–60 帧）
- 多主题像素银河背景与闪烁星星动画
- 横向或纵向无缝循环银河背景

## 安装

建议使用 Python 3.12 或更高版本。

```bash
pip install -r requirements.txt
```

项目的直接运行依赖为 Pillow。开发时使用的 Conda 环境名称可以是 `torch`，但项目本身不依赖 PyTorch。

每次成功生成都会在本地 `.generated_seeds/` 中登记 seed 与图像参数。该目录默认不会提交到 Git。

### 输出路径

未指定路径时，四种生成方式分别使用以下默认目录：

```text
output/planet/<风格>-<seed>/
output/planet_animation/<风格>-<seed>/
output/galaxy/<主题>-<seed>/
output/galaxy_animation/<主题>-<seed>/
```

静态生成可通过 `filename`（星球）或 `output`（银河）指定完整文件路径。动画生成可通过 `output_dir` 指定目录，并通过 `filename_prefix` 指定帧名前缀；帧序号统一为 `frame000`、`frame001` 等三位格式。显式指定的路径始终优先于默认路径，父目录会自动创建。

## 快速开始

### 启动图形界面

在项目使用的 `torch` Conda 环境中运行：

```bash
conda activate torch
python gui_server.py
```

程序会启动仅监听本机的轻量服务，并使用系统当前默认浏览器打开网页。界面支持静态星球、星球动画、静态银河和银河动画，可预览生成结果，也可通过系统窗口选择输出目录。不希望自动打开浏览器时可运行 `python gui_server.py --no-browser`，再访问 `http://127.0.0.1:8765/`。

GUI 的默认输出目录使用项目相对路径，并以只读方式显示。点击“选择路径”会调用系统文件资源管理器选择文件夹；程序会根据生成类型、风格、seed 和帧序号自动补全 PNG 文件名。选择时允许使用绝对路径，结果会保存在本地 `.gui_settings.json`，下次启动自动恢复，也可以点击“恢复默认”清除。界面右上角可以直接切换中文和 English。

界面文案分别保存在 `locales/zh-CN.json` 和 `locales/en-US.json`。新增语言时可复制任一文件并翻译同名键值，例如保存为 `locales/ja-JP.json`，同时修改其中的 `language.name`。程序会自动扫描合法命名的 JSON，新语言重新打开网页后会出现在右上角列表中；也可以通过 `?lang=ja-JP` 直接指定。语言文件不存在时会回退到中文。

### Windows 打包版本

已构建的 Windows 成品位于：

```text
package/
├─ PixelPlanetGenerator-Full/
│  ├─ PixelPlanetGenerator-Full.exe
│  ├─ locales/
│  ├─ output/
│  ├─ _internal/
│  └─ 使用说明.txt
└─ PixelPlanetGenerator-Simple/
   ├─ PixelPlanetGenerator-Simple.exe
   ├─ locales/
   ├─ output/
   ├─ _internal/
   └─ 使用说明.txt
```

双击对应 EXE 即可启动。程序会在本机运行图像生成服务，并使用系统当前默认浏览器打开网页。完整版默认使用端口 `18765`，简易版默认使用 `18766`；端口被占用时会自动选择其他可用端口。

每个发布目录都是一个完整程序，移动或分发时应保留整个目录，不能只复制 EXE，也不要删除 `_internal`。`locales` 和 `output` 均位于 EXE 旁：

- `locales`：用户可以修改现有语言，或添加新的语言 JSON。
- `output`：使用默认路径时，生成的 PNG 和动画帧保存在这里，用户可以直接访问。
- `.gui_settings.json`：用户选择自定义输出目录后自动创建，用于下次启动恢复路径。

### 完整版与简易版差异

| 功能 | 完整版 | 简易版 |
|---|---:|---:|
| 静态星球生成 | 支持 | 支持 |
| 静态银河生成 | 支持 | 支持 |
| 星球动画 | 支持，单次 15–60 帧 | 不支持 |
| 银河动画 | 支持，单次 15–60 帧 | 不支持 |
| 内置星球风格与银河主题 | 支持 | 支持 |
| 自定义星球配色 | 支持 | 不支持 |
| 自定义银河配色 | 支持 | 不支持 |
| seed 范围 | 自动 seed 为 `0–999999`；手动 seed 可使用任意整数 | 固定为 `0–49` |
| 每个风格的固定 seed 数 | 不固定；自动池包含 1,000,000 个候选 seed | 50 个 |
| 避免重复生成 | 支持 | 不提供 |
| 光环、四角边框、无缝方向等选项 | 支持 | 支持 |
| 中英文与外部语言文件 | 支持 | 支持 |
| 自定义输出目录 | 支持 | 支持 |

简易版的限制不只是在网页中隐藏：服务端也会拒绝动画、自定义风格以及 `0–49` 以外的 seed，因此无法通过直接调用接口绕过。“每个风格 50 个 seed”指 seed 值固定为 50 个；尺寸、光环、边框等其他参数仍可改变最终图片。

如需从源码启动简易模式，可运行：

```bash
python gui_server.py --edition simple --port 8766
```

### 重新打包

安装 PyInstaller 后，在 Windows PowerShell 中运行：

```powershell
python -m pip install pyinstaller
.\build_packages.ps1
```

脚本会清理并重新创建 `package` 文件夹中的完整版和简易版。构建默认使用项目配置的 `torch` 环境；如果 Python 路径不同，可以显式传入：

```powershell
.\build_packages.ps1 -Python "C:\path\to\python.exe"
```

当前发布包使用 Pillow 原生完成地形混合，不依赖 PyTorch 或 NumPy。完整版和简易版各约 37 MB。

### 生成单个星球

```python
from planet import make_planet

seed = make_planet(
    size=96,
    tone="earth",
    filename="my_planet.png",
    seed=12345,
    ring=True,
    ring_color="#00FFFF",
    frame=True,
)
print(seed)
```

`size` 是基础像素尺寸；最终输出会按 `scale` 放大，默认是 4 倍。相同参数和 seed 会得到相同的星球。

### 自定义星球风格

传入 `custom_palette` 可以替代内置风格。它必须提供 **2 个海洋色、3 个陆地色和 1 个光环色**；每种颜色可使用 `"#RRGGBB"`、`"#RGB"` 或 `(R, G, B)`。

```python
custom_palette = {
    "sea": ["#182848", "#4B6CB7"],
    "land": ["#355C2D", "#6E9E45", "#BEDF75"],
    "ringcolor": "#FFD166",
}

make_planet(filename="custom_planet.png", custom_palette=custom_palette)
```

### 避免重复生成

四个生成函数都支持 `ensure_unique=True`。开启后，系统会对生成类型、seed 和所有影响图像的参数进行本地查重；显式使用已生成的配置会报错，自动 seed 则会重新抽取未登记的 seed。

```python
make_planet(filename="unique.png", seed=None, ensure_unique=True)
```

### 生成星球自转动画

```python
from planet_animation import generate_animation

seed, frames = generate_animation(
    tone="ice",
    size=96,
    frames=24,
    seed=42,
    ring=True,
    output_dir="animation_output",
)
```

函数会输出编号 PNG 帧，适合导入 Godot、Unity、Aseprite 或视频工具。`frames` 必须在 15 到 60 之间。

### 生成银河背景

```python
from galaxy_generator import generate_pixel_galaxy

path, theme, flash_count, seed = generate_pixel_galaxy(
    width=800,
    height=450,
    pixel_size=3,
    output="galaxy.png",
    theme_name="deep_blue",
    seamless_axis="horizontal",
    flash_stars=15,
    seed=101,
)
```

`seamless_axis` 可选值：

- `None`：普通背景
- `"horizontal"`：左右无缝循环
- `"vertical"`：上下无缝循环

银河主题包括：`deep_blue`、`red_nebula`、`white_bright`、`purple_magenta`、`cold_white`。

### 自定义银河风格

传入 `custom_theme` 可以替代内置主题。它必须提供 **2 个背景色、3 个星云色和 3 个银河带色**：

```python
custom_theme = {
    "name": "sunset_space",  # 可选
    "bg_top": "#12031A",
    "bg_bottom": "#3A103A",
    "nebula": ["#7B2CBF", "#C77DFF", "#FFB4E6"],
    "galaxy": ["#FFC6FF", "#FFE5EC", "#FFFFFF"],
}

generate_pixel_galaxy(output="custom_galaxy.png", custom_theme=custom_theme)
```

### 生成银河动画

```python
from galaxy_generator import generate_galaxy_animation

frames, theme, flash_count, seed = generate_galaxy_animation(
    width=800,
    height=450,
    pixel_size=3,
    output_dir="galaxy_animation",
    theme_name="purple_magenta",
    seamless_axis="horizontal",
    flash_stars=20,
    frames=24,
    seed=456,
)
```

## 批量生成

`main.py` 默认运行星球自转动画示例：

```bash
python main.py
```

如需按所有星球风格批量输出状态图，将 `main.py` 底部的 `main()` 调用取消注释，并按需要关闭动画示例。

## 项目结构

```text
Pixel-Planet-Generator/
├─ planet.py              # 静态星球渲染
├─ planet_animation.py    # 星球自转动画
├─ galaxy_generator.py    # 银河背景与动画
├─ palettes.py            # 星球调色板
├─ galaxy_color_themes.py # 银河主题
├─ blob_map.py            # 地形噪声
├─ ring.py / frame.py     # 光环与边框
├─ recolor.py             # 后处理滤镜
├─ main.py                # 示例入口与批量生成
├─ gui_server.py          # 本地图形界面与生成 API
├─ ui_prototype.html      # 图形界面页面
├─ locales/zh-CN.json     # 图形界面中文文案
├─ locales/en-US.json     # 图形界面英文文案
├─ full_launcher.py       # 完整版发布入口
├─ simple_launcher.py     # 简易版发布入口
├─ build_packages.ps1     # Windows 双版本构建脚本
├─ package/               # 已构建的完整版与简易版
└─ requirements.txt       # 运行依赖
```

## Git 约定

生成的 PNG、动画帧、缓存、编辑器配置和本地备份均由 `.gitignore` 排除。源码、调色板、依赖清单与文档应作为版本控制内容提交。
