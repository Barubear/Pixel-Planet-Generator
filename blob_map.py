"""
blob_map.py — 地形噪声生成

生成"类大陆"结构的灰度地形图：
  低分辨率随机噪声 → 双三次放大 + 高斯模糊（大尺度结构）
  + 全分辨率随机噪声 + 高斯模糊（细节）
  75% / 25% 混合

随机数序列与原逐像素实现完全一致（同一 seed → 同一地形）。
"""

import random

from PIL import Image, ImageFilter


def _random_gray_bytes(rng, count):
    """从 rng 按顺序取 count 个 0-255 灰度值（与原逐像素实现序列一致）。"""
    out = bytearray()
    while count:
        chunk = min(4096, count)
        for _ in range(chunk):
            out.append(rng.randint(0, 255))
        count -= chunk
    return bytes(out)


def random_blob_map(size, seed=None):
    if seed is None:
        seed = random.randint(0, 999999)

    rng = random.Random(seed)
    base_size = max(8, size // 8)

    # 大尺度结构：低分辨率随机 → 放大 → 模糊
    noise = Image.new("L", (base_size, base_size))
    noise.frombytes(_random_gray_bytes(rng, base_size * base_size))
    noise = noise.resize((size, size), Image.Resampling.BICUBIC)
    noise = noise.filter(ImageFilter.GaussianBlur(radius=size * 0.06))

    # 细节层：同一 rng 继续取数（保持与旧实现相同的随机序列）
    detail = Image.new("L", (size, size))
    detail.frombytes(_random_gray_bytes(rng, size * size))
    detail = detail.filter(ImageFilter.GaussianBlur(radius=size * 0.015))

    # Pillow 原生混合，避免仅为这一操作引入 NumPy 与大型数学运行库。
    return Image.blend(noise, detail, 0.25), seed
