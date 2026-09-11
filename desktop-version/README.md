# Pixel Art Planet Generator — 本地版

本地程序在系统默认浏览器中打开生成界面。当前界面与网页版共用 JavaScript 渲染器，生成、预览和 ZIP 打包均在浏览器完成。保留的 Python/Pillow 脚本接口见本文后半部分，其算法、参数和输出规则与当前界面独立。

## 启动

在本目录打开终端，使用项目的 `torch` 环境：

```bash
conda activate torch
pip install -r requirements.txt
python gui_server.py
```

项目不依赖 PyTorch，Python 脚本的直接依赖为 Pillow。使用 `python gui_server.py --no-browser` 可不自动打开浏览器，再访问 `http://127.0.0.1:8765/`。

简易模式：

```bash
python gui_server.py --edition simple --port 8766
```

## 当前界面用法

- 星球基础尺寸为 48–192，放大倍数为 1–8；放大不改变地形。海洋占比为 30%–90%，每 10% 一档。
- 银河宽高为 64–1024；星星数量占比为 30%–90%，每 10% 一档，默认 60%。这里是相对密度，不是亮点覆盖面积。
- 银河无缝方向只控制边缘拼接。动画中普通星星固定位置闪烁，不随无缝方向移动；中心漩涡默认关闭，开启后单独旋转。
- 动画支持 15–60 帧，导出 PNG 帧序列，不直接导出 GIF 或视频。
- 行星环、角标边框可选。内置风格使用统一默认边框颜色；按下色更深，不可按下色为灰色。自定义配色只显示已启用效果对应的选色项。
- 开启角标边框及变色版本后，随机或避免重复生成无印、悬浮、按下、不可按下四套图；复现仅生成后三套。未开启变色版本则只生成当前选定效果的一套。
- 点击保存后才下载：单张为 PNG，多张或动画为 ZIP。保存位置完全由浏览器决定，不自动写入程序旁的 `output`，没有预先选择保存目录或恢复默认目录的功能。

### Seed 与文件夹查询

默认完全随机，每次抽取一个 Seed，不保证不重复。复现只使用输入的第一个 Seed，其余忽略；未填写会弹窗提示。保持风格、尺寸、配色和其他参数一致，才能复现原图。

避免重复把输入框视为排除列表，多个 Seed 用半角逗号分隔，同时排除当前页面已生成的同类 Seed。一次仍只生成一个 Seed，不支持批量复现。页面内的生成记录刷新后清空，不通过 Cookie 或 `.generated_seeds/` 保存。

自动查询仅在避免重复模式出现，没有默认目录。用户选择文件夹并授权后递归按名称查询，结果替换输入框内容，可继续编辑。支持如 `earth-123.png`、`galaxy_animation-deep_blue-123.zip`；不读取 ZIP 内部，也不能识别当前按钮状态套图文件名，这些 Seed 需手动补充。

目录选择受浏览器支持和权限限制。若“下载”等系统目录被拒绝，请在其中新建普通子文件夹再选择；不支持选择时仍可手动输入 Seed。选择的文件夹只用于读取 Seed，不决定下载位置。

## Windows 发行包

当前已存在的程序：

```text
package/
├─ PixelPlanetGenerator-Full/
│  └─ PixelPlanetGenerator-Full.exe
└─ PixelArtPlanetGenerator-Lite/
   └─ PixelPlanetGenerator-Simple.exe
```

双击 EXE 后在默认浏览器打开。完整版默认端口为 `18765`，简易版为 `18766`，被占用时自动选择其他可用端口。移动或分发时保留整个目录，包括 `_internal`、`web_app` 和 `locales`，不能只复制 EXE。

### 完整版与简易版

| 功能 | 完整版 | 简易版 |
|---|---|---|
| 静态星球、银河 | 支持 | 支持 |
| 星球、银河动画 | 15–60 帧 | 不支持 |
| 自定义配色 | 支持 | 不支持 |
| Seed 范围 | 0–2147483647 | 0–49，每个风格 50 个 |
| 避免重复与文件夹查询 | 支持 | 支持，生成范围为 0–49 |
| 比例、行星环、角标状态套图、无缝方向 | 支持 | 支持 |
| 中英文、外部生成界面语言文件 | 支持 | 支持 |
| PNG / ZIP 下载 | 支持 | 支持 |

简易版的 50 个 Seed 不代表最多只能输出 50 张图片，其他参数仍可调整。避免重复排除完 50 个 Seed 后会提示没有可用 Seed；请调整排除列表或重新打开页面。

## 语言文件

生成界面的外部文案位于程序旁的 `locales/zh-CN.json` 和 `locales/en-US.json`，两个版本均可修改或添加语言。复制现有 JSON，使用如 `ja-JP.json` 的语言代码命名，并翻译键值、修改 `language.name`，刷新生成页面后从右上角选择。

语言选择保存在浏览器本地存储中；不可用的语言回退到中文。没有页面内导入语言包按钮。使用说明等独立页面使用 `web_app/js/locales.js` 中的内置翻译，编辑外部 JSON 不会自动改变这些页面。

## 重新打包

```powershell
python -m pip install pyinstaller
.\build_packages.ps1
```

默认使用项目配置的 `torch` Python；也可指定：

```powershell
.\build_packages.ps1 -Python "C:\path\to\python.exe"
```

脚本会清理并重建发布目录，请先备份自行添加的语言包和个人文件。当前脚本输出的简易版目录名为 `PixelPlanetGenerator-Simple`，不同于现有的 `PixelArtPlanetGenerator-Lite` 目录。发布包体积以实际构建结果为准。

## 保留的 Python 脚本接口

以下示例不经过浏览器渲染器，相同 Seed 不保证与网页版或当前桌面界面的结果一致。成功生成会在 `.generated_seeds/` 登记 Seed 与参数；`ensure_unique=True` 对类型、Seed 和影响图像的参数查重，这与页面内的 Seed 排除列表不同。

四种生成方式在未指定路径时使用：

```text
output/planet/<风格>-<seed>/
output/planet_animation/<风格>-<seed>/
output/galaxy/<主题>-<seed>/
output/galaxy_animation/<主题>-<seed>/
```

静态生成通过 `filename`（星球）或 `output`（银河）指定完整路径；动画通过 `output_dir` 指定目录、`filename_prefix` 指定帧名前缀，帧序号为 `frame000` 等三位格式。显式路径优先，父目录自动创建。这些路径不适用于浏览器保存按钮。

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
├─ web_app/               # 当前浏览器界面、渲染器与说明页面
├─ ui_prototype.html      # 保留的旧界面（非默认入口）
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
