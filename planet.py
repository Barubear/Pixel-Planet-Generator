from PIL import Image
import random
import math

from palettes import PALETTES
from blob_map import random_blob_map
from ring import draw_ring
from frame import draw_corner_frame

def make_planet(
    size=96,
    tone="earth",
    filename="planet.png",
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
):
    if seed is None:
        seed = random.randint(0, 999999)

    rng = random.Random(seed)

    palette = PALETTES.get(tone, PALETTES["earth"])
    terrain, used_seed = random_blob_map(size, seed)

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    cx = cy = size / 2
    radius = size * 0.263

    if ring:
        if ring_color is None:
            ring_color = parse_color(palette["ringcolor"])
        else:
            ring_color = parse_color(ring_color)

        draw_ring(
            img,
            cx,
            cy,
            radius,
            ring_color,
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
            ring_color,
            front=True,
            tilt=ring_tilt,
            width=ring_width,
        )
    if frame:
        draw_corner_frame(
            img,
            color=frame_color,
            corner_size=frame_size,
            thickness=frame_thickness,
            padding=frame_padding
        )

    img = img.resize((size * scale, size * scale), Image.Resampling.NEAREST)
    img.save(filename)

    print(f"saved: {filename}")
    print(f"seed: {used_seed}")

    return used_seed


def parse_color(color):
    """
    支持：
    (255, 255, 255)
    "#FFFFFF"
    "#FFF"
    """
    if color is None:
        return None

    # 已经是 RGB tuple
    if isinstance(color, tuple) and len(color) == 3:
        return color

    # HEX 字符串
    if isinstance(color, str):
        color = color.lstrip("#")

        # 短格式 #FFF
        if len(color) == 3:
            color = "".join([c * 2 for c in color])

        if len(color) != 6:
            raise ValueError("Invalid HEX color")

        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)

        return (r, g, b)

    raise ValueError(f"Unsupported color format: {color}")