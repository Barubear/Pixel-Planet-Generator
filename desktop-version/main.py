from pathlib import Path

from palettes import PALETTES
from planet import make_planet
from recolor import recolor_planet
from galaxy_generator import generate_pixel_galaxy
from planet_animation import generate_animation


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


def run_animation_prototype(
    tone="earth",
    frames=24,
    seed=12345,
    size=96,
    ring=True,
    ring_color="#00FFFF",
    frame=False,
    frame_color="#00FFFF",
    scale=4,
    output_dir="animation_output",
):
    """
    测试自转动画原型。

    参数:
      tone: 星球风格 (earth/desert/lava/toxic/ice/ocean/alien/forest/gas/mono)
      frames: 帧数 (15-60)
      seed: 随机种子 (同一 seed 生成相同动画)
      size: 基础尺寸
      ring: 是否带光环
      ring_color: 光环颜色 (HEX 或 RGB tuple)
      frame: 是否带四角边框
      frame_color: 边框颜色
      scale: 输出缩放倍率
      output_dir: 输出目录

    示例:
      run_animation_prototype(tone="lava", frames=30, seed=99999, ring=True)
      run_animation_prototype(tone="ice", frames=15, seed=42)
      run_animation_prototype(tone="alien", frames=60, seed=7, ring=True, ring_color="#FF00FF")
    """
    seed, paths = generate_animation(
        size=size,
        tone=tone,
        output_dir=output_dir,
        frames=frames,
        seed=seed,
        ring=ring,
        ring_color=ring_color,
        frame=frame,
        frame_color=frame_color,
        scale=scale,
        filename_prefix=f"{tone}_spin",
    )
    print(f"\n=== 动画原型完成 ===")
    print(f"风格: {tone}")
    print(f"帧数: {len(paths)}")
    print(f"种子: {seed}")
    print(f"输出: {Path(output_dir).resolve()}")
    print(f"首帧: {paths[0]}")
    print(f"尾帧: {paths[-1]}")
    return seed, paths


if __name__ == "__main__":
    # 批量生成所有风格
    # main()

    # 自转动画原型
    run_animation_prototype(
        tone="earth",
        frames=24,
        seed=12345,
        ring=True,
        ring_color="#00FFFF",
    )
