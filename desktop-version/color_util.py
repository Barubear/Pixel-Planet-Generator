"""
color_util.py — 公共颜色解析工具
"""


def parse_color(color):
    """
    将颜色统一解析为 (R, G, B) tuple。

    支持:
      - (255, 255, 255)       → 直接返回
      - "#FFFFFF"             → (255, 255, 255)
      - "#FFF"                → (255, 255, 255)
      - None                  → None

    不支持的格式抛出 ValueError。
    """
    if color is None:
        return None

    if isinstance(color, tuple) and len(color) == 3:
        if not all(
            isinstance(channel, int)
            and not isinstance(channel, bool)
            and 0 <= channel <= 255
            for channel in color
        ):
            raise ValueError(f"RGB channels must be integers from 0 to 255: {color!r}")
        return color

    if isinstance(color, str):
        color = color.lstrip("#")
        if len(color) == 3:
            color = "".join(c * 2 for c in color)
        if len(color) != 6:
            raise ValueError(f"Invalid HEX color: #{color}")
        try:
            return (
                int(color[0:2], 16),
                int(color[2:4], 16),
                int(color[4:6], 16),
            )
        except ValueError as error:
            raise ValueError(f"Invalid HEX color: #{color}") from error

    raise ValueError(f"Unsupported color format: {color!r}")
