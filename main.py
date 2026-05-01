from pathlib import Path

from palettes import PALETTES
from planet import make_planet
from recolor import recolor_planet
from galaxy_generator import generate_pixel_galaxy

def main():
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)


    #seed = make_planet( size=96, tone="earth", filename="single_earth.png", ring=True, ring_color="#00FFFF")

    #size = 96

    

    generate_pixel_galaxy(
        width=800,
        height=450,
        pixel_size=3,
        output=output_dir /f"galaxy_red.png",
        theme_name="red_nebula",
    )

    generate_pixel_galaxy(
        width=800,
        height=450,
        pixel_size=3,
        output=output_dir /f"galaxy_random.png",
        theme_name="random",
    )


if __name__ == "__main__":
    main()