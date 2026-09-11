from PIL import Image


def recolor_planet(image_path, mode="grayscale", output="out.png"):
    img = Image.open(image_path).convert("RGBA")
    pixels = img.load()

    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = pixels[x, y]

            if a == 0:
                continue

            brightness = int(0.299 * r + 0.587 * g + 0.114 * b)

            if mode == "grayscale":
                pixels[x, y] = (brightness, brightness, brightness, a)

            elif mode == "purple":
                pr = min(255, int(brightness * 1.2))
                pg = int(brightness * 0.4)
                pb = min(255, int(brightness * 1.5))

                pixels[x, y] = (pr, pg, pb, a)

            else:
                raise ValueError(f"Unknown recolor mode: {mode}")

    img.save(output)
    print(f"saved: {output}")