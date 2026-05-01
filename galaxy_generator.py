from PIL import Image, ImageDraw, ImageFilter
import random
import math
from galaxy_color_themes import COLOR_THEMES

BASE_W, BASE_H = 320, 180




def lerp(a, b, t):
    return a + (b - a) * t


def color_lerp(c1, c2, t):
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))


def soft_palette_color(colors):
    t = random.random() * (len(colors) - 1)
    i = int(t)
    local_t = t - i

    if i >= len(colors) - 1:
        return colors[-1]

    # 平滑过渡
    local_t = local_t * local_t * (3 - 2 * local_t)
    return color_lerp(colors[i], colors[i + 1], local_t)


def random_star_color():
    star_colors = [
        (255, 255, 255),
        (245, 245, 235),
        (230, 240, 255),
        (255, 230, 210),
        (255, 190, 160),
        (190, 220, 255),
    ]

    base = random.choice(star_colors)
    brightness = random.uniform(0.75, 1.0)

    return tuple(min(255, int(c * brightness)) for c in base) + (255,)


def generate_pixel_galaxy(
    width=800,
    height=450,
    pixel_size=3,
    output="galaxy_colorful.png",
    theme_name=None
):
    scale = min(width / BASE_W, height / BASE_H)
    area_scale = (width * height) / (BASE_W * BASE_H)

    if theme_name == None:
        theme = random.choice(COLOR_THEMES)
    else:
        for t in COLOR_THEMES:
            if t["name"] == theme_name:
                theme = t

    galaxy_angle = random.uniform(-0.55, 0.55)
    galaxy_width = random.uniform(0.08, 0.17) * height
    nebula_strength = random.uniform(0.6, 1.6)
    star_density = random.uniform(0.75, 1.35)

    img = Image.new("RGB", (width, height), theme["bg_top"])
    draw = ImageDraw.Draw(img)

    # 背景柔和渐变
    for y in range(height):
        t = y / height
        t = t * t * (3 - 2 * t)
        color = color_lerp(theme["bg_top"], theme["bg_bottom"], t)
        draw.line([(0, y), (width, y)], fill=color)

    # 星云
    nebula = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    ndraw = ImageDraw.Draw(nebula)

    nebula_count = int(16 * area_scale * nebula_strength)

    for _ in range(nebula_count):
        x = random.randint(-int(width * 0.25), width)
        y = random.randint(-int(height * 0.25), height)

        rx = int(random.randint(35, 150) * scale)
        ry = int(random.randint(25, 100) * scale)

        color = soft_palette_color(theme["nebula"])
        alpha = random.randint(20, 70)

        ndraw.ellipse((x, y, x + rx, y + ry), fill=(*color, alpha))

    nebula = nebula.filter(ImageFilter.GaussianBlur(radius=max(1, 7 * scale)))
    img = Image.alpha_composite(img.convert("RGBA"), nebula)

    # 银河带
    galaxy = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(galaxy)

    center_y = random.randint(int(height * 0.3), int(height * 0.7))
    particle_count = int(2100 * area_scale)

    for _ in range(particle_count):
        x = random.randint(0, width - 1)

        base_y = center_y + math.tan(galaxy_angle) * (x - width / 2)
        wave = math.sin(x * 0.018 + random.random() * 4) * height * 0.035
        y = int(base_y + wave + random.gauss(0, galaxy_width))

        if 0 <= y < height:
            color = soft_palette_color(theme["galaxy"])

            brightness = random.uniform(0.65, 1.15)
            color = tuple(min(255, int(c * brightness)) for c in color)

            alpha = random.randint(35, 105)
            gdraw.point((x, y), fill=(*color, alpha))

    galaxy = galaxy.filter(ImageFilter.GaussianBlur(radius=max(1, 1.4 * scale)))
    img = Image.alpha_composite(img, galaxy)

    draw = ImageDraw.Draw(img)

    # 普通星星
    star_count = int(300 * area_scale * star_density)

    for _ in range(star_count):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)

        color = random_star_color()

        # 大多数暗一点，少数很亮
        if random.random() < 0.75:
            factor = random.uniform(0.45, 0.85)
            color = tuple(int(c * factor) for c in color[:3]) + (255,)

        draw.point((x, y), fill=color)

    # 少量亮星
    bright_star_count = max(2, int(4 * area_scale))

    for _ in range(bright_star_count):
        x = random.randint(3, width - 4)
        y = random.randint(3, height - 4)

        color = random.choice([
            (255, 255, 255, 255),
            (245, 245, 230, 255),
            (225, 240, 255, 255),
            (255, 220, 190, 255),
        ])

        style = random.choices(
            ["dot", "diamond", "tiny_cluster"],
            weights=[35, 40, 25],
            k=1
        )[0]

        if style == "dot":
            draw.point((x, y), fill=color)
            if random.random() < 0.45:
                draw.point((x + 1, y), fill=color)

        elif style == "diamond":
            soft = (*color[:3], 120)

            draw.point((x, y), fill=color)
            draw.point((x - 1, y), fill=color)
            draw.point((x + 1, y), fill=color)
            draw.point((x, y - 1), fill=color)
            draw.point((x, y + 1), fill=color)

            draw.point((x - 1, y - 1), fill=soft)
            draw.point((x + 1, y - 1), fill=soft)
            draw.point((x - 1, y + 1), fill=soft)
            draw.point((x + 1, y + 1), fill=soft)

        elif style == "tiny_cluster":
            for _ in range(random.randint(3, 6)):
                dx = random.randint(-2, 2)
                dy = random.randint(-2, 2)

                if dx * dx + dy * dy <= 5:
                    alpha = random.randint(120, 255)
                    draw.point((x + dx, y + dy), fill=(*color[:3], alpha))

    img = img.convert("RGB")
    img = img.resize(
        (width * pixel_size, height * pixel_size),
        Image.Resampling.NEAREST
    )

    img.save(output)
    print(f"生成完成：{output}")
    print(f"本次主题：{theme['name']}")


if __name__ == "__main__":
    generate_pixel_galaxy(
        width=800,
        height=450,
        pixel_size=3,
        output="galaxy_colorful.png"
    )