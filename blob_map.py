from PIL import Image, ImageFilter
import random


def random_blob_map(size, seed=None):
    if seed is None:
        seed = random.randint(0, 999999)

    rng = random.Random(seed)

    base_size = max(8, size // 8)
    noise = Image.new("L", (base_size, base_size))

    for y in range(base_size):
        for x in range(base_size):
            noise.putpixel((x, y), rng.randint(0, 255))

    noise = noise.resize((size, size), Image.Resampling.BICUBIC)
    noise = noise.filter(ImageFilter.GaussianBlur(radius=size * 0.06))

    detail = Image.new("L", (size, size))

    for y in range(size):
        for x in range(size):
            detail.putpixel((x, y), rng.randint(0, 255))

    detail = detail.filter(ImageFilter.GaussianBlur(radius=size * 0.015))

    result = Image.new("L", (size, size))

    for y in range(size):
        for x in range(size):
            v = noise.getpixel((x, y)) * 0.75 + detail.getpixel((x, y)) * 0.25
            result.putpixel((x, y), int(v))

    return result, seed