import math


def draw_ring(img, cx, cy, radius, color, front=True, tilt=0.42, width=0.28):
    pixels = img.load()
    w, h = img.size

    outer_rx = radius * 1.75
    outer_ry = radius * tilt
    inner_rx = radius * (1.75 - width)
    inner_ry = radius * max(0.08, tilt - width * 0.45)

    for y in range(h):
        for x in range(w):
            dx = x - cx
            dy = y - cy

            outer = (dx / outer_rx) ** 2 + (dy / outer_ry) ** 2
            inner = (dx / inner_rx) ** 2 + (dy / inner_ry) ** 2

            if inner > 1 and outer < 1:
                if not front and dy > 0:
                    continue

                if front and dy < 0:
                    continue

                dist = math.sqrt(dx * dx + dy * dy)

                if not front and dist < radius:
                    continue

                alpha = int(170 * (1 - abs(outer - 0.75)))
                alpha = max(50, min(170, alpha))

                pixels[x, y] = (color[0], color[1], color[2], alpha)