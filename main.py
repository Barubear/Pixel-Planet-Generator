from pathlib import Path

from palettes import PALETTES
from planet import make_planet
from recolor import recolor_planet
from galaxy_generator import generate_pixel_galaxy

def main():
    output_dir = Path("plant_output")
    output_dir.mkdir(exist_ok=True)
    size=96
    plant_vol = 50
    for plant_tone in PALETTES:
        tone_dir = output_dir / plant_tone
        tone_dir.mkdir(exist_ok=True)
        for num in range(plant_vol):
            basefilename = f"{plant_tone}_{num}" 
            plant_dir = tone_dir / basefilename
            plant_dir.mkdir(exist_ok=True)
            filename = basefilename +"_normal.png"
            file_path = plant_dir / filename
            ring  = num <= (plant_vol/2-1)
            seed = make_planet( size=96, tone=plant_tone, filename=file_path,ring=ring)
            plant_make_packet(size,seed,plant_tone, plant_dir,basefilename,ring)


    # seed = make_planet( size=96, tone="desert", filename="single_desert_normal.png", ring_color="#00FFFF")
    # make_planet( size=96, tone="desert", filename="single_desert_hover.png", ring_color="#00FFFF",seed=seed, frame=True,frame_color="#ff0033")
    # make_planet( size=96, tone="desert", filename="single_desert_pressed.png",  ring_color="#00FFFF",seed=seed, frame=True,frame_color="#990000")
    # make_planet( size=96, tone="desert", filename="single_desert_disable.png", ring_color="#00FFFF",seed=seed, frame=True,frame_color="#660000")
    # #size = 96

    

    # generate_pixel_galaxy(
    #     width=int(1920/2),
    #     height=int(1080/2),
    #     pixel_size=3,
    #     output=output_dir /f"galaxy_red.png",
    #     theme_name="red_nebula",
    # )



def plant_make_packet(size,seed,tone,plant_dir,basefilename,ring):
    filename = basefilename +"_hover.png"
    file_path = plant_dir / filename
    make_planet( size=size, tone=tone, filename= file_path , seed=seed, frame=True,frame_color="#ff0033",ring=ring)
    filename = basefilename +"_pressed.png"
    file_path = plant_dir / filename
    make_planet( size=size, tone=tone, filename=file_path, seed=seed, frame=True,frame_color="#990000",ring=ring)
    filename = basefilename +"_disable.png"
    file_path = plant_dir / filename
    make_planet( size=size, tone=tone, filename=file_path, seed=seed, frame=True,frame_color="#660000",ring=ring)


if __name__ == "__main__":
    main()