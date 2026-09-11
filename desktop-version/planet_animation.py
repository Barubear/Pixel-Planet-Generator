"""
planet_animation.py — 像素星球自转动画帧渲染

核心思路：
  1. 生成一张"展开的球面贴图"（equirectangular map），宽度 = 2 * size（覆盖 360° 经度）
  2. 每帧按 roll_offset（0..2π）取样：经度 = π + (x/size)*π + roll_offset
  3. 用 sin(经度) 做球面收敛，保证圆盘边缘自然压缩
  4. 光照方向固定（左上光源），不随旋转变化
  5. 输出 N 帧独立 PNG（帧数 15-60）
"""

from pathlib import Path
from PIL import Image, ImageFilter
import random
import math

from palettes import PALETTES
from planet import _resolve_palette
from seed_registry import prepare_seed, record_generation
from output_paths import resolve_animation_frame_path
from ring import draw_ring
from blob_map import random_blob_map
from frame import draw_corner_frame
from color_util import parse_color

MIN_FRAMES = 15
MAX_FRAMES = 60


def _make_unwrapped_terrain(size, seed):
    """
    生成展开的球面地形贴图。
    返回 (terrain_img, used_seed)：
      terrain_img: L 模式，尺寸 (2*size, size)，x=0 和 x=2*size 对应同一经度（0°）
    """
    rng = random.Random(seed)

    # 低分辨率随机噪声，宽度是高度的 2 倍（球面展开比例）
    base_w = max(16, size // 4)
    base_h = max(8, size // 8)
    noise = Image.new("L", (base_w, base_h))

    for y in range(base_h):
        for x in range(base_w):
            noise.putpixel((x, y), rng.randint(0, 255))

    # 横向三联平铺后再放大、模糊并裁取中央周期，避免经度 0°/360° 接缝。
    tiled_noise = Image.new("L", (base_w * 3, base_h))
    for index in range(3):
        tiled_noise.paste(noise, (index * base_w, 0))
    tiled_noise = tiled_noise.resize((size * 6, size), Image.Resampling.BICUBIC)
    tiled_noise = tiled_noise.filter(ImageFilter.GaussianBlur(radius=size * 0.06))
    noise = tiled_noise.crop((size * 2, 0, size * 4, size))

    # 细节层
    detail = Image.new("L", (size * 2, size))
    for y in range(size):
        for x in range(size * 2):
            detail.putpixel((x, y), rng.randint(0, 255))
    tiled_detail = Image.new("L", (size * 6, size))
    for index in range(3):
        tiled_detail.paste(detail, (index * size * 2, 0))
    tiled_detail = tiled_detail.filter(ImageFilter.GaussianBlur(radius=size * 0.015))
    detail = tiled_detail.crop((size * 2, 0, size * 4, size))

    # 混合
    result = Image.new("L", (size * 2, size))
    rpx = result.load()
    npx = noise.load()
    dpx = detail.load()
    for y in range(size):
        for x in range(size * 2):
            v = npx[x, y] * 0.75 + dpx[x, y] * 0.25
            rpx[x, y] = int(v)

    return result, seed


def render_frame(
    terrain,
    size,
    tone,
    roll_offset,
    ring=False,
    ring_color=None,
    ring_tilt=0.42,
    ring_width=0.28,
    frame=False,
    frame_color="#00FFFF",
    frame_size=12,
    frame_thickness=2,
    frame_padding=4,
    scale=4,
    land_level=None,
    seed_for_rng=None,
    custom_palette=None,
):
    """
    渲染单帧。

    参数:
      terrain: 展开地形图 (2*size, size) L 模式
      size: 基础尺寸
      tone: 调色板名称
      roll_offset: 经度偏移（弧度，0..2π）
      ring/frame: 与 make_planet 相同
      land_level: 海陆阈值（None 时自动取 134）
      seed_for_rng: 用于像素级随机抖动（保持各帧风格一致）
    """
    if land_level is None:
        land_level = 134

    palette = _resolve_palette(tone, custom_palette)
    rng = random.Random(seed_for_rng if seed_for_rng is not None else 42)

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    cx = cy = size / 2
    radius = size * 0.263

    # 先画光环后半（球体后面）
    if ring:
        if ring_color is None:
            ring_color = parse_color(palette["ringcolor"])
        else:
            ring_color = parse_color(ring_color)
        draw_ring(img, cx, cy, radius, ring_color, front=False, tilt=ring_tilt, width=ring_width)

    # 渲染球体
    tpx = terrain.load()
    tw = terrain.width  # 2 * size

    for y in range(size):
        dy = y - cy
        for x in range(size):
            dx = x - cx
            dist = math.sqrt(dx * dx + dy * dy)

            if dist > radius:
                continue

            nx = dx / radius
            ny = dy / radius

            # 球面展开采样
            # 经度范围: π 到 2π（正面半球），加上 roll_offset 旋转
            # 屏幕 x → 经度: lon = π + (nx * π/2) + roll_offset  (nx ∈ [-1, 1])
            # 用 sin(lon) 做球面收敛
            lon = math.pi + nx * (math.pi / 2) + roll_offset
            # 取样 x: 经度 0 对应 terrain x=0, 经度 2π 对应 terrain x=2*size
            tx = ((lon / (2 * math.pi)) % 1.0) * tw
            tx = int(tx) % tw
            ty = y

            v = tpx[tx, ty]

            edge = 1 - dist / radius
            light = 0.65 + 0.35 * max(0, (-nx - ny + 1) / 2)

            if v > land_level:
                color = rng.choice(palette["land"])
            else:
                color = rng.choice(palette["sea"])

            if abs(v - land_level) < 7:
                color = tuple(min(255, int(c * 1.35)) for c in color)

            jitter = rng.uniform(0.85, 1.15)
            shade = light * (0.55 + edge * 0.45) * jitter

            r = min(255, int(color[0] * shade))
            g = min(255, int(color[1] * shade))
            b = min(255, int(color[2] * shade))

            img.putpixel((x, y), (r, g, b, 255))

    # 光环前半
    if ring:
        draw_ring(img, cx, cy, radius, ring_color, front=True, tilt=ring_tilt, width=ring_width)

    # 角框
    if frame:
        draw_corner_frame(img, color=frame_color, corner_size=frame_size,
                          thickness=frame_thickness, padding=frame_padding)

    # 缩放
    img = img.resize((size * scale, size * scale), Image.Resampling.NEAREST)
    return img


def generate_animation(
    size=96,
    tone="earth",
    output_dir=None,
    frames=24,
    seed=None,
    ring=False,
    ring_color=None,
    frame=False,
    frame_color="#00FFFF",
    scale=4,
    filename_prefix=None,
    custom_palette=None,
    ensure_unique=False,
    seed_registry_dir=".generated_seeds",
    ring_tilt=0.42,
    ring_width=0.28,
    frame_size=12,
    frame_thickness=2,
    frame_padding=4,
):
    """
    生成自转动画帧序列。

    参数:
      size: 基础像素尺寸（96）
      tone: 风格
      output_dir: 输出目录
      frames: 帧数（15-60）
      seed: 随机种子
      ring/ring_color/frame/frame_color/custom_palette: 同 make_planet
      scale: 输出缩放倍率
      filename_prefix: 文件名前缀

    返回:
      (used_seed, [frame_paths])
    """
    if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
        raise ValueError("size 必须是正整数")
    if not isinstance(scale, int) or isinstance(scale, bool) or scale <= 0:
        raise ValueError("scale 必须是正整数")
    if not isinstance(frames, int) or isinstance(frames, bool):
        raise ValueError("frames 必须是整数")
    if not (MIN_FRAMES <= frames <= MAX_FRAMES):
        raise ValueError(f"frames 必须在 {MIN_FRAMES}-{MAX_FRAMES} 之间，当前: {frames}")
    if ring and not (0 < ring_tilt <= 1):
        raise ValueError("ring_tilt 必须在 0 到 1 之间")
    if ring and not (0 < ring_width < 1.75):
        raise ValueError("ring_width 必须在 0 到 1.75 之间")
    if frame:
        frame_values = (frame_size, frame_thickness, frame_padding)
        if not all(isinstance(value, int) and not isinstance(value, bool) for value in frame_values):
            raise ValueError("frame_size、frame_thickness 和 frame_padding 必须是整数")
        if frame_size <= 0 or frame_thickness <= 0 or frame_padding < 0:
            raise ValueError("边框尺寸和粗细必须为正数，padding 不能为负数")
        if frame_padding + max(frame_size, frame_thickness) > size:
            raise ValueError("边框尺寸超出图片范围")

    palette = _resolve_palette(tone, custom_palette)
    resolved_ring_color = None
    if ring:
        resolved_ring_color = parse_color(
            palette["ringcolor"] if ring_color is None else ring_color
        )
    resolved_frame_color = parse_color(frame_color) if frame else None

    def seed_parameters(candidate):
        return {
            "size": size,
            "tone": tone if custom_palette is None else None,
            "seed": candidate,
            "frames": frames,
            "ring": ring,
            "ring_color": resolved_ring_color,
            "ring_tilt": ring_tilt if ring else None,
            "ring_width": ring_width if ring else None,
            "frame": frame,
            "frame_color": resolved_frame_color,
            "frame_size": frame_size if frame else None,
            "frame_thickness": frame_thickness if frame else None,
            "frame_padding": frame_padding if frame else None,
            "scale": scale,
            "custom_palette": palette if custom_palette is not None else None,
        }

    seed = prepare_seed("planet_animation", seed, seed_parameters, ensure_unique, seed_registry_dir)

    print(f"生成自转动画: tone={tone}, frames={frames}, seed={seed}")

    # 1. 生成展开地形
    terrain, used_seed = _make_unwrapped_terrain(size, seed)
    print(f"  地形生成完成 (seed={used_seed})")

    # 2. 确定海陆阈值（从地形中位数取）
    px = terrain.load()
    values = sorted(px[x, y] for x in range(terrain.width) for y in range(terrain.height))
    land_level = values[len(values) // 2]
    # 稍微偏一点让陆地占 ~40%
    land_level = max(100, min(170, land_level - 10))
    print(f"  海陆阈值: {land_level}")

    # 3. 逐帧渲染
    frame_paths = []
    two_pi = 2 * math.pi
    for i in range(frames):
        # 均匀分布的旋转角，确保循环无缝
        roll = (i / frames) * two_pi
        img = render_frame(
            terrain=terrain,
            size=size,
            tone=tone,
            roll_offset=roll,
            ring=ring,
            ring_color=resolved_ring_color,
            ring_tilt=ring_tilt,
            ring_width=ring_width,
            frame=frame,
            frame_color=resolved_frame_color,
            frame_size=frame_size,
            frame_thickness=frame_thickness,
            frame_padding=frame_padding,
            scale=scale,
            land_level=land_level,
            seed_for_rng=used_seed,  # 每帧相同的抖动序列
            custom_palette=custom_palette,
        )
        style_name = "custom" if custom_palette is not None else tone
        path = resolve_animation_frame_path(
            "planet_animation",
            style_name,
            used_seed,
            i,
            output_dir=output_dir,
            filename_prefix=filename_prefix,
        )
        img.save(path)
        frame_paths.append(str(path))
        if (i + 1) % 10 == 0 or i == frames - 1:
            print(f"  帧 {i + 1}/{frames} 完成")

    print(f"完成！输出目录: {Path(frame_paths[0]).parent}")
    record_generation("planet_animation", used_seed, seed_parameters(used_seed), seed_registry_dir)
    return used_seed, frame_paths


if __name__ == "__main__":
    generate_animation(
        size=96,
        tone="earth",
        output_dir="animation_output",
        frames=24,
        seed=12345,
        ring=True,
        ring_color="#00FFFF",
        scale=4,
        filename_prefix="earth_spin",
    )

