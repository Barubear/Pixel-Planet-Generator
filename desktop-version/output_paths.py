"""统一管理生成图片的默认路径和用户自定义路径。"""

from pathlib import Path
import re
import sys


APPLICATION_ROOT = (
    Path(sys.executable).resolve().parent
    if getattr(sys, "frozen", False)
    else Path(__file__).resolve().parent
)
OUTPUT_ROOT = APPLICATION_ROOT / "output"


def _safe_style_name(style):
    """将风格名转换为跨平台可用的目录和文件名片段。"""
    name = str(style).strip() or "custom"
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)


def _default_output_dir(kind, style, seed):
    """返回某种生成方式的默认输出目录。"""
    style = _safe_style_name(style)
    return OUTPUT_ROOT / kind / f"{style}-{seed}"


def resolve_static_output_path(kind, style, seed, output=None, output_dir=None):
    """解析静态图片路径；显式传入的路径优先于默认路径。

    默认：output/<kind>/<style>-<seed>/<style>-<seed>.png
    """
    style = _safe_style_name(style)
    stem = f"{style}-{seed}"
    if output is not None and output_dir is not None:
        raise ValueError("不能同时指定完整输出文件和输出目录")
    if output is not None:
        path = Path(output)
    elif output_dir is not None:
        path = Path(output_dir) / f"{stem}.png"
    else:
        path = _default_output_dir(kind, style, seed) / f"{stem}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def resolve_animation_frame_path(
    kind,
    style,
    seed,
    frame_index,
    output_dir=None,
    filename_prefix=None,
):
    """解析动画帧路径；动画默认拥有独立目录。

    默认：output/<kind>/<style>-<seed>/<style>-<seed>-frame000.png
    """
    style = _safe_style_name(style)
    stem = f"{style}-{seed}"
    folder = Path(output_dir) if output_dir is not None else _default_output_dir(kind, style, seed)
    prefix = _safe_style_name(filename_prefix) if filename_prefix is not None else stem
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"{prefix}-frame{frame_index:03d}.png"
