from pathlib import Path

from palettes import PALETTES
from planet import make_planet
from recolor import recolor_planet


def main():
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    size = 96

    for tone in PALETTES.keys():
        normal_path = output_dir / f"{tone}.png"
        gray_path = output_dir / f"{tone}_gray.png"
        purple_path = output_dir / f"{tone}_purple.png"
        ring_path = output_dir / f"{tone}_ring.png"

        # 每个风格固定一个 seed
        # 这样普通版、灰色版、紫色版都来自同一颗星球
        seed = make_planet(
            size=size,
            tone=tone,
            filename=normal_path,
            ring=False,
        )

        recolor_planet(
            image_path=normal_path,
            mode="grayscale",
            output=gray_path,
        )

        recolor_planet(
            image_path=normal_path,
            mode="purple",
            output=purple_path,
        )

        # 光环版使用同一个 seed，地表会和普通版一致
        make_planet(
            size=size,
            tone=tone,
            filename=ring_path,
            seed=seed,
            ring=True,
        )


if __name__ == "__main__":
    main()