from PIL import Image, ImageDraw, ImageFilter
import random
import random as random_module
import math
from pathlib import Path
from galaxy_color_themes import COLOR_THEMES
from color_util import parse_color
from seed_registry import prepare_seed, record_generation
from output_paths import resolve_animation_frame_path, resolve_static_output_path

BASE_W, BASE_H = 320, 180

# 闪烁星星数量上限
FLASH_MAX_COUNT = 50


def lerp(a, b, t):
    return a + (b - a) * t


def color_lerp(c1, c2, t):
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))


def soft_palette_color(colors, rng=None):
    """从调色板平滑取色；未传 rng 时保留原有独立调用行为。"""
    rng = rng or random
    t = rng.random() * (len(colors) - 1)
    i = int(t)
    local_t = t - i

    if i >= len(colors) - 1:
        return colors[-1]

    # 平滑过渡
    local_t = local_t * local_t * (3 - 2 * local_t)
    return color_lerp(colors[i], colors[i + 1], local_t)


def random_star_color(rng=None):
    """生成随机星色；未传 rng 时使用模块级随机源。"""
    rng = rng or random
    star_colors = [
        (255, 255, 255),
        (245, 245, 235),
        (230, 240, 255),
        (255, 230, 210),
        (255, 190, 160),
        (190, 220, 255),
    ]

    base = rng.choice(star_colors)
    brightness = rng.uniform(0.75, 1.0)

    return tuple(min(255, int(c * brightness)) for c in base) + (255,)


def _resolve_theme(theme_name, custom_theme, rng):
    """返回内置主题或严格校验后的自定义银河主题。"""
    if custom_theme is None:
        if theme_name is None:
            return rng.choice(COLOR_THEMES)
        for theme in COLOR_THEMES:
            if theme["name"] == theme_name:
                return theme
        raise ValueError(f"未知主题：{theme_name}")

    required = {"bg_top", "bg_bottom", "nebula", "galaxy"}
    missing = required - custom_theme.keys()
    if missing:
        raise ValueError(f"custom_theme 缺少字段: {', '.join(sorted(missing))}")
    if len(custom_theme["nebula"]) != 3:
        raise ValueError("custom_theme['nebula'] 必须恰好包含 3 个颜色")
    if len(custom_theme["galaxy"]) != 3:
        raise ValueError("custom_theme['galaxy'] 必须恰好包含 3 个颜色")

    return {
        "name": custom_theme.get("name", "custom"),
        "bg_top": parse_color(custom_theme["bg_top"]),
        "bg_bottom": parse_color(custom_theme["bg_bottom"]),
        "nebula": [parse_color(color) for color in custom_theme["nebula"]],
        "galaxy": [parse_color(color) for color in custom_theme["galaxy"]],
    }


def _wrap_offsets(w, h, seamless_axis=None):
    """返回仅沿指定循环轴复制图形所需的偏移。"""
    if seamless_axis == "horizontal":
        return [(-w, 0), (0, 0), (w, 0)]
    if seamless_axis == "vertical":
        return [(0, -h), (0, 0), (0, h)]
    return [(0, 0)]


def _tile_for_blur(img, w, h, axis):
    """沿循环轴三联平铺，返回平铺图及其中心原图的裁剪区域。"""
    if axis is None:
        return img, (0, 0, w, h)
    if axis == "horizontal":
        big = Image.new("RGBA", (w * 3, h), (0, 0, 0, 0))
        for i in range(3):
            big.paste(img, (i * w, 0))
        return big, (w, 0, w * 2, h)

    big = Image.new("RGBA", (w, h * 3), (0, 0, 0, 0))
    for i in range(3):
        big.paste(img, (0, i * h))
    return big, (0, h, w, h * 2)


def _draw_wrapped(draw, x, y, w, h, fill, seamless_axis=None):
    """在指定轴循环绘制一个像素点，另一轴保持边界裁剪。"""
    if seamless_axis == "horizontal":
        x %= w
    elif seamless_axis == "vertical":
        y %= h

    if 0 <= x < w and 0 <= y < h:
        draw.point((x, y), fill=fill)


def _draw_wrapped_ellipse(draw, cx, cy, rx, ry, w, h, fill, seamless_axis=None):
    """在画布上以循环方式绘制椭圆（与后续统一模糊配合使用）。"""
    for dx, dy in _wrap_offsets(w, h, seamless_axis):
        draw.ellipse(
            (cx + dx, cy + dy, cx + dx + rx, cy + dy + ry),
            fill=fill
        )


def _make_star_sprite(size, core_radius=1, glow_radius=2, base_color=(255, 255, 255, 255)):
    """创建闪烁星星精灵。

    返回一张 RGBA 图，中心是核心亮点，外围有柔和光晕。
    """
    sprite = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(sprite)
    center = size // 2

    # 核心亮点
    d.point((center, center), fill=base_color)

    # 周围 8 方向
    if size >= 5:
        soft_color = (*base_color[:3], 180)
        d.point((center - 1, center), fill=soft_color)
        d.point((center + 1, center), fill=soft_color)
        d.point((center, center - 1), fill=soft_color)
        d.point((center, center + 1), fill=soft_color)

        if size >= 7:
            corner_color = (*base_color[:3], 120)
            d.point((center - 1, center - 1), fill=corner_color)
            d.point((center + 1, center - 1), fill=corner_color)
            d.point((center - 1, center + 1), fill=corner_color)
            d.point((center + 1, center + 1), fill=corner_color)

    # 高斯模糊制造光晕
    if glow_radius > 0:
        sprite = sprite.filter(ImageFilter.GaussianBlur(radius=glow_radius * 0.5))

    return sprite


def _apply_flash_effects(img, flash_stars, frame_idx, total_frames, seamless_axis=None):
    """将闪烁星星叠加到图像上。

    flash_stars: list of dicts with keys:
      x, y, color, period, phase, sprite
    """
    w, h = img.size
    result = img.copy()
    for star in flash_stars:
        x, y = star["x"], star["y"]
        color = star["color"]
        period = star["period"]
        phase = star["phase"]

        # 亮度随时间变化：0..1 之间
        brightness = 0.5 + 0.5 * math.sin(2 * math.pi * (frame_idx / total_frames) * period + phase)
        brightness = max(0.0, min(1.0, brightness))

        if brightness < 0.05:
            continue

        # 缩放 alpha
        sprite = star["sprite"]
        # 应用 alpha
        if sprite.mode == "RGBA":
            r, g, b, a = sprite.split()
            a = a.point(lambda p: int(p * brightness))
            sprite = Image.merge("RGBA", (r, g, b, a))

        # 循环绘制
        if seamless_axis is not None:
            for dx, dy in _wrap_offsets(w, h, seamless_axis):
                px = x + dx
                py = y + dy
                result.paste(sprite, (px - sprite.width // 2, py - sprite.height //  2), sprite)
        else:
            result.paste(sprite, (x - sprite.width // 2, y - sprite.height // 2), sprite)

    return result


def _compute_frame_count(total_stars, flash_stars, base_frames=24):
    """根据闪烁星星数量计算所需帧数。

    规则：
      - 基础帧数 24
      - 每增加 5 颗闪烁星星，帧数 +1
      - 上限 60 帧
    """
    extra = (flash_stars + 4) // 5
    return min(60, base_frames + extra)


def _validate_galaxy_parameters(
    width,
    height,
    pixel_size,
    seamless_axis,
    flash_stars,
    frames=None,
):
    for name, value in (("width", width), ("height", height), ("pixel_size", pixel_size)):
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValueError(f"{name} 必须是正整数")
    if seamless_axis not in (None, "horizontal", "vertical"):
        raise ValueError(
            f"seamless_axis 必须是 None / 'horizontal' / 'vertical'，当前: {seamless_axis!r}"
        )
    if flash_stars is not None:
        if not isinstance(flash_stars, int) or isinstance(flash_stars, bool):
            raise ValueError("flash_stars 必须是整数或 None")
        if not 0 <= flash_stars <= FLASH_MAX_COUNT:
            raise ValueError(f"flash_stars 必须在 0-{FLASH_MAX_COUNT} 之间")
    if frames is not None:
        if not isinstance(frames, int) or isinstance(frames, bool):
            raise ValueError("frames 必须是整数或 None")
        if not 15 <= frames <= 60:
            raise ValueError("frames 必须在 15-60 之间")


def _build_galaxy_scene(
    width,
    height,
    seamless_axis,
    flash_stars,
    theme_name,
    custom_theme,
    random,
):
    # 计算总星星数量
    star_density = random.uniform(0.75, 1.35)
    total_star_count = int(300 * (width * height) / (BASE_W * BASE_H) * star_density)

    # 计算帧数
    if flash_stars > 0:
        total_frames = _compute_frame_count(total_star_count, flash_stars)
    else:
        total_frames = 1

    theme = _resolve_theme(theme_name, custom_theme, random)

    # 生成图像
    scale = min(width / BASE_W, height / BASE_H)
    area_scale = (width * height) / (BASE_W * BASE_H)

    galaxy_angle = random.uniform(-0.55, 0.55)
    galaxy_width = random.uniform(0.08, 0.17) * height
    nebula_strength = random.uniform(0.6, 1.6)

    img = Image.new("RGB", (width, height), theme["bg_top"])
    draw = ImageDraw.Draw(img)

    # 背景柔和渐变
    # 纵向循环时沿水平方向渐变（保证上下边缘颜色一致，可无缝拼接）
    if seamless_axis == "vertical":
        for x in range(width):
            t = x / width
            t = t * t * (3 - 2 * t)
            color = color_lerp(theme["bg_top"], theme["bg_bottom"], t)
            draw.line([(x, 0), (x, height)], fill=color)
    else:
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

        color = soft_palette_color(theme["nebula"], random)
        alpha = random.randint(20, 70)

        if seamless_axis is not None:
            _draw_wrapped_ellipse(ndraw, x, y, rx, ry, width, height, (*color, alpha), seamless_axis)
        else:
            ndraw.ellipse((x, y, x + rx, y + ry), fill=(*color, alpha))

    # 周期性模糊：平铺 3x3 后模糊再取中间，保证边缘不产生暗带
    if seamless_axis is not None:
        tiled, crop_box = _tile_for_blur(nebula, width, height, seamless_axis)
        nebula_radius = max(1, min(7 * scale, width / 4, height / 4))
        tiled = tiled.filter(ImageFilter.GaussianBlur(radius=nebula_radius))
        nebula = tiled.crop(crop_box)
    else:
        nebula = nebula.filter(ImageFilter.GaussianBlur(radius=max(1, 7 * scale)))
    img = Image.alpha_composite(img.convert("RGBA"), nebula)

    # 银河带
    galaxy = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(galaxy)

    center_y = random.randint(int(height * 0.3), int(height * 0.7))
    particle_count = int(2100 * area_scale)

    for _ in range(particle_count):
        # 循环模式下粒子范围扩展到画布外，保证边缘密度连续
        if seamless_axis == "horizontal":
            x = random.randint(-width, width * 2 - 1)
        else:
            x = random.randint(0, width - 1)

        base_y = center_y + math.tan(galaxy_angle) * (x - width / 2)
        wave = math.sin(x * 0.018 + random.random() * 4) * height * 0.035
        y = int(base_y + wave + random.gauss(0, galaxy_width))

        if seamless_axis == "vertical" or 0 <= y < height:
            color = soft_palette_color(theme["galaxy"], random)

            brightness = random.uniform(0.65, 1.15)
            color = tuple(min(255, int(c * brightness)) for c in color)

            alpha = random.randint(35, 105)
            if seamless_axis is not None:
                _draw_wrapped(gdraw, x, y, width, height, (*color, alpha), seamless_axis)
            else:
                gdraw.point((x, y), fill=(*color, alpha))

    # 周期性模糊：平铺 3x3 后模糊，再取中间，保证边缘不产生暗带
    if seamless_axis is not None:
        tiled, crop_box = _tile_for_blur(galaxy, width, height, seamless_axis)
        tiled = tiled.filter(ImageFilter.GaussianBlur(radius=max(1, 1.4 * scale)))
        galaxy = tiled.crop(crop_box)
    else:
        galaxy = galaxy.filter(ImageFilter.GaussianBlur(radius=max(1, 1.4 * scale)))
    img = Image.alpha_composite(img, galaxy)

    draw = ImageDraw.Draw(img)

    # 普通星星
    static_star_count = total_star_count - flash_stars
    if static_star_count < 0:
        static_star_count = 0

    for _ in range(static_star_count):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)

        color = random_star_color(random)

        # 大多数暗一点，少数很亮
        if random.random() < 0.75:
            factor = random.uniform(0.45, 0.85)
            color = tuple(int(c * factor) for c in color[:3]) + (255,)

        if seamless_axis is not None:
            _draw_wrapped(draw, x, y, width, height, color, seamless_axis)
        else:
            draw.point((x, y), fill=color)

    # 少量亮星
    bright_star_count = max(2, int(4 * area_scale))

    for _ in range(bright_star_count):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)

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
            if seamless_axis is not None:
                _draw_wrapped(draw, x, y, width, height, color, seamless_axis)
            else:
                draw.point((x, y), fill=color)
            if random.random() < 0.45:
                if seamless_axis is not None:
                    _draw_wrapped(draw, x + 1, y, width, height, color, seamless_axis)
                else:
                    draw.point((x + 1, y), fill=color)

        elif style == "diamond":
            soft = (*color[:3], 120)

            if seamless_axis is not None:
                _draw_wrapped(draw, x, y, width, height, color, seamless_axis)
                _draw_wrapped(draw, x - 1, y, width, height, color, seamless_axis)
                _draw_wrapped(draw, x + 1, y, width, height, color, seamless_axis)
                _draw_wrapped(draw, x, y - 1, width, height, color, seamless_axis)
                _draw_wrapped(draw, x, y + 1, width, height, color, seamless_axis)

                _draw_wrapped(draw, x - 1, y - 1, width, height, soft, seamless_axis)
                _draw_wrapped(draw, x + 1, y - 1, width, height, soft, seamless_axis)
                _draw_wrapped(draw, x - 1, y + 1, width, height, soft, seamless_axis)
                _draw_wrapped(draw, x + 1, y + 1, width, height, soft, seamless_axis)
            else:
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
                    if seamless_axis is not None:
                        _draw_wrapped(draw, x + dx, y + dy, width, height, (*color[:3], alpha), seamless_axis)
                    else:
                        draw.point((x + dx, y + dy), fill=(*color[:3], alpha))

    # 创建闪烁星星精灵
    flash_star_list = []
    if flash_stars > 0:
        for i in range(flash_stars):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)

            color = random.choice([
                (255, 255, 255),
                (245, 245, 230),
                (225, 240, 255),
                (255, 220, 190),
            ])

            # 周期：2-8 个周期
            period = random.randint(2, 8)
            phase = random.uniform(0, 2 * math.pi)

            # 创建精灵
            sprite = _make_star_sprite(7, base_color=(*color, 255))

            flash_star_list.append({
                "x": x,
                "y": y,
                "color": color,
                "period": period,
                "phase": phase,
                "sprite": sprite,
            })
    return img, theme, flash_star_list, total_frames


def generate_pixel_galaxy(
    width=800,
    height=450,
    pixel_size=3,
    output=None,
    theme_name=None,
    seamless_axis=None,
    flash_stars=None,
    seed=None,
    custom_theme=None,
    ensure_unique=False,
    seed_registry_dir=".generated_seeds",
    output_dir=None,
):
    """生成静态像素银河背景并返回 (路径, 主题, 闪烁星数量, seed)。"""
    _validate_galaxy_parameters(
        width, height, pixel_size, seamless_axis, flash_stars
    )
    if flash_stars is None:
        flash_stars = int(FLASH_MAX_COUNT * 0.3)

    def seed_parameters(candidate):
        return {
            "width": width, "height": height, "pixel_size": pixel_size,
            "theme_name": theme_name, "seamless_axis": seamless_axis,
            "flash_stars": flash_stars, "seed": candidate,
            "custom_theme": custom_theme,
        }

    seed = prepare_seed("galaxy", seed, seed_parameters, ensure_unique, seed_registry_dir)
    random = random_module.Random(seed)
    img, theme, flash_star_list, total_frames = _build_galaxy_scene(
        width,
        height,
        seamless_axis,
        flash_stars,
        theme_name,
        custom_theme,
        random,
    )

    # 静态图展示闪烁动画第 0 帧，避免 flash_stars 只扣减普通星却不绘制。
    if flash_star_list:
        img = _apply_flash_effects(
            img, flash_star_list, frame_idx=0, total_frames=total_frames,
            seamless_axis=seamless_axis,
        )

    img = img.convert("RGB").resize(
        (width * pixel_size, height * pixel_size),
        Image.Resampling.NEAREST,
    )
    output_path = resolve_static_output_path(
        "galaxy", theme["name"], seed, output, output_dir
    )
    img.save(output_path)
    record_generation("galaxy", seed, seed_parameters(seed), seed_registry_dir)

    print(f"生成完成：{output_path}")
    print(f"本次主题：{theme['name']}")
    print(f"随机种子：{seed}")
    return str(output_path), theme["name"], flash_stars, seed


def generate_galaxy_animation(
    width=800,
    height=450,
    pixel_size=3,
    output_dir=None,
    theme_name=None,
    seamless_axis=None,
    flash_stars=None,
    frames=None,
    seed=None,
    custom_theme=None,
    ensure_unique=False,
    seed_registry_dir=".generated_seeds",
    filename_prefix=None,
):
    """生成银河动画帧并返回 (帧路径, 主题, 闪烁星数量, seed)。"""
    _validate_galaxy_parameters(
        width, height, pixel_size, seamless_axis, flash_stars, frames
    )
    if flash_stars is None:
        flash_stars = int(FLASH_MAX_COUNT * 0.3)
    if frames is None:
        frames = _compute_frame_count(0, flash_stars)

    def seed_parameters(candidate):
        return {
            "width": width, "height": height, "pixel_size": pixel_size,
            "theme_name": theme_name, "seamless_axis": seamless_axis,
            "flash_stars": flash_stars, "frames": frames, "seed": candidate,
            "custom_theme": custom_theme,
        }

    seed = prepare_seed(
        "galaxy_animation", seed, seed_parameters, ensure_unique, seed_registry_dir
    )
    random = random_module.Random(seed)
    base_img, theme, flash_star_list, _ = _build_galaxy_scene(
        width,
        height,
        seamless_axis,
        flash_stars,
        theme_name,
        custom_theme,
        random,
    )

    print(
        f"生成动画：theme={theme['name']}, frames={frames}, "
        f"flash={flash_stars}, seed={seed}"
    )
    frame_paths = []
    for frame_idx in range(frames):
        img = base_img.copy()
        if flash_star_list:
            img = _apply_flash_effects(
                img,
                flash_star_list,
                frame_idx,
                frames,
                seamless_axis,
            )
        img = img.convert("RGB").resize(
            (width * pixel_size, height * pixel_size),
            Image.Resampling.NEAREST,
        )
        path = resolve_animation_frame_path(
            "galaxy_animation",
            theme["name"],
            seed,
            frame_idx,
            output_dir=output_dir,
            filename_prefix=filename_prefix,
        )
        img.save(path)
        frame_paths.append(str(path))
        if (frame_idx + 1) % 10 == 0 or frame_idx == frames - 1:
            print(f"  帧 {frame_idx + 1}/{frames} 完成")

    print(f"动画生成完成！输出目录：{Path(frame_paths[0]).parent}")
    record_generation(
        "galaxy_animation", seed, seed_parameters(seed), seed_registry_dir
    )
    return frame_paths, theme["name"], flash_stars, seed


if __name__ == "__main__":
    # 测试 1: 无循环
    generate_pixel_galaxy(
        width=800,
        height=450,
        pixel_size=3,
        output="galaxy_test_no_seamless.png",
        seed=123,
    )

    # 测试 2: 水平循环
    generate_pixel_galaxy(
        width=800,
        height=450,
        pixel_size=3,
        output="galaxy_test_horizontal.png",
        seamless_axis="horizontal",
        seed=123,
    )

    # 测试 3: 垂直循环
    generate_pixel_galaxy(
        width=450,
        height=800,
        pixel_size=3,
        output="galaxy_test_vertical.png",
        seamless_axis="vertical",
        seed=123,
    )

    # 测试 4: 动画
    generate_galaxy_animation(
        width=800,
        height=450,
        pixel_size=3,
        output_dir="galaxy_anim_test",
        theme_name="deep_blue",
        seamless_axis="horizontal",
        flash_stars=20,
        seed=456,
    )
