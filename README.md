# 🌍 Pixel Planet Generator / 像素星球生成器

A lightweight procedural pixel-art planet generator built with Python and Pillow.  
一个基于 Python + Pillow 的轻量级程序化像素星球生成器。

---

## ✨ Features / 功能特点

- 🎨 Multiple planet styles (earth, lava, ice, alien, etc.)  
  多种星球风格（地球、熔岩、冰冻、外星等）

- 🌍 Continent-like terrain generation  
  类大陆结构的随机地形生成

- 🪐 Optional ring system (Saturn-like)  
  可选光环系统（类似土星）

- 🎭 Post-processing filters (grayscale / purple)  
  后处理滤镜（灰度 / 紫色）

- 🔁 Seed-based reproducibility  
  支持种子复现生成结果

- 🧩 Modular code structure  
  模块化结构，易扩展

---

## 📁 Project Structure / 项目结构

```text
planet_generator/
├─ palettes.py     # Color presets / 调色板
├─ blob_map.py     # Terrain generation / 地形生成
├─ ring.py         # Ring rendering / 光环绘制
├─ planet.py       # Planet generator / 星球生成
├─ recolor.py      # Filters / 滤镜
└─ main.py         # Batch generation / 批量生成
```

## ▶️ Usage / 使用方法
Batch generation / 批量生成
```text
python main.py
```
输出在：
```text
output/
```
每种风格包含：
```text
earth.png
earth_gray.png
earth_purple.png
earth_ring.png
```

## 🧪 Single Planet Example / 单个星球示例

Generate one planet, then recolor it.
生成一个星球，并生成不同颜色版本。

```python
from planet import make_planet
from recolor import recolor_planet

seed = make_planet( size=96, tone="earth", filename="single_earth.png", ring=False, )
recolor_planet( image_path="single_earth.png", mode="grayscale", output="single_earth_gray.png", )
recolor_planet( image_path="single_earth.png", mode="purple", output="single_earth_purple.png", )
print("Seed:", seed)
```


With ring / 带光环版本


```python
from planet import make_planet
from recolor import recolor_planet

seed = make_planet( size=96, tone="ice", filename="single_ice_ring.png",  ring=True, ring_tilt=0.35, ring_width=0.3, )
print("Seed:", seed)
```
## 🎨 Available Styles / 可用风格

| Style| Description | 
|-----|-----|
|earth |	类地行星 |
|desert |	沙漠星 |
|lava |	熔岩星 |
|toxic |	有毒星 |
|ice |	冰冻星 |
|ocean |	海洋星 |
|alien |	外星风格 |
|forest |	森林星 |
|gas |	气态风 |
|mono |	单色 |


## 🪐 Ring Parameters / 光环参数

| Parameter| Description | 
|-----|-----|
ring |	Enable ring / 开启光环 |
ring_tilt |	Ellipse tilt / 倾斜度 |
ring_width |	Ring thickness / 宽度 |


## 🔁 Seed System / 种子系统

```python
make_planet(seed=123456)
```

Same seed = same planet
相同 seed = 完全一致


