from PIL import Image
import random
import math

from palettes import PALETTES
from blob_map import random_blob_map
from ring import draw_ring
from frame import draw_corner_frame
from color_util import parse_color
from seed_registry import prepare_seed, record_generation
from output_paths import resolve_static_output_path


def _resolve_palette(tone, custom_palette):
    """返回内置或严格校验后的自定义星球调色板。"""
    if custom_palette is None:
        if tone not in PALETTES:
            raise ValueError(f"未知星球风格：{tone!r}；可选值: {', '.join(PALETTES)}")
        return PALETTES[tone]

    required = {"sea", "land", "ringcolor"}
    missing = required - custom_palette.keys()
    if missing:
        raise ValueError(f"custom_palette 缺少字段: {', '.join(sorted(missing))}")
    if len(custom_palette["sea"]) != 2:
        raise ValueError("custom_palette['sea'] 必须恰好包含 2 个颜色")
    if len(custom_palette["land"]) != 3:
        raise ValueError("custom_palette['land'] 必须恰好包含 3 个颜色")

    return {
        "sea": [parse_color(color) for color in custom_palette["sea"]],
        "land": [parse_color(color) for color in custom_palette["land"]],
        "ringcolor": parse_color(custom_palette["ringcolor"]),
    }


def make_planet(
    size=96,
    tone="earth",
    filename=None,
    seed=None,
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
    custom_palette=None,
    ensure_unique=False,
    seed_registry_dir=".generated_seeds",
    output_dir=None,
):
    if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
        raise ValueError("size 必须是正整数")
    if not isinstance(scale, int) or isinstance(scale, bool) or scale <= 0:
        raise ValueError("scale 必须是正整数")
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
            "ring": ring,
            "ring_color": resolved_ring_color,
            "ring_tilt": ring_tilt if ring else None,
            "ring_width": ring_width if ring else None,
            "frame": frame,
            "frame_color": resolved_frame_color,
            "frame_size": frame_size if frame else None,
            "frame_thickness": frame_thickness if frame else None,
            "frame_padding": frame_padding if frame else None,
            "scale": scale, "custom_palette": palette if custom_palette is not None else None,
        }

    seed = prepare_seed("planet", seed, seed_parameters, ensure_unique, seed_registry_dir)

    rng = random.Random(seed)

    terrain, used_seed = random_blob_map(size, seed)

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    cx = cy = size / 2
    radius = size * 0.263

    if ring:
        draw_ring(
            img,
            cx,
            cy,
            radius,
            resolved_ring_color,
            front=False,
            tilt=ring_tilt,
            width=ring_width,
        )

    land_level = rng.randint(118, 150)

    for y in range(size):
        for x in range(size):
            dx = x - cx
            dy = y - cy
            dist = math.sqrt(dx * dx + dy * dy)

            if dist > radius:
                continue

            nx = dx / radius
            ny = dy / radius

            v = terrain.getpixel((x, y))

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

    if ring:
        draw_ring(
            img,
            cx,
            cy,
            radius,
            resolved_ring_color,
            front=True,
            tilt=ring_tilt,
            width=ring_width,
        )
    if frame:
        draw_corner_frame(
            img,
            color=resolved_frame_color,
            corner_size=frame_size,
            thickness=frame_thickness,
            padding=frame_padding
        )

    img = img.resize((size * scale, size * scale), Image.Resampling.NEAREST)
    style_name = "custom" if custom_palette is not None else tone
    output_path = resolve_static_output_path(
        "planet", style_name, used_seed, filename, output_dir
    )
    img.save(output_path)
    record_generation("planet", used_seed, seed_parameters(used_seed), seed_registry_dir)

    print(f"saved: {output_path}")
    print(f"seed: {used_seed}")

    return used_seed
