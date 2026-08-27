from color_util import parse_color


def draw_corner_frame(
    img,
    color="#00FFFF",
    corner_size=12,
    thickness=2,
    padding=4,
):
    color = parse_color(color)
    pixels = img.load()
    w, h = img.size

    for i in range(corner_size):
        for t in range(thickness):
            # top-left
            pixels[padding + i, padding + t] = (*color, 255)
            pixels[padding + t, padding + i] = (*color, 255)

            # top-right
            pixels[w - padding - 1 - i, padding + t] = (*color, 255)
            pixels[w - padding - 1 - t, padding + i] = (*color, 255)

            # bottom-left
            pixels[padding + i, h - padding - 1 - t] = (*color, 255)
            pixels[padding + t, h - padding - 1 - i] = (*color, 255)

            # bottom-right
            pixels[w - padding - 1 - i, h - padding - 1 - t] = (*color, 255)
            pixels[w - padding - 1 - t, h - padding - 1 - i] = (*color, 255)
