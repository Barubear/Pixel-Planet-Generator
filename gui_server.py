"""Pixel Planet Generator 的本地图形界面服务。"""

from argparse import ArgumentParser
from collections import OrderedDict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from queue import Empty, Queue
import re
import secrets
import os
import sys
from threading import Event, Lock, Thread, get_ident
from urllib.parse import urlsplit
import webbrowser

from galaxy_generator import generate_galaxy_animation, generate_pixel_galaxy
from output_paths import resolve_static_output_path
from planet import make_planet
from planet_animation import generate_animation


PROJECT_ROOT = (
    Path(sys.executable).resolve().parent
    if getattr(sys, "frozen", False)
    else Path(__file__).resolve().parent
)
UI_PATH = PROJECT_ROOT / "ui_prototype.html"
LOCALE_ROOT = PROJECT_ROOT / "locales"
SETTINGS_PATH = PROJECT_ROOT / ".gui_settings.json"
MAX_REQUEST_BYTES = 1_000_000
MAX_PREVIEW_FILES = 500
OUTPUT_SETTING_KEYS = {
    "planet_static",
    "planet_animation",
    "galaxy_static",
    "galaxy_animation",
}
EDITION_FULL = "full"
EDITION_SIMPLE = "simple"
SIMPLE_SEEDS = tuple(range(50))

_preview_files = OrderedDict()
_preview_lock = Lock()
_settings_lock = Lock()
_native_dialog_requests = Queue()
_native_dialog_owner_thread = None


def _optional_text(value):
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _optional_relative_path(value):
    """将 GUI 输入的项目内相对路径解析成绝对路径。"""
    value = _optional_text(value)
    if value is None:
        return None
    path = Path(value)
    if path.is_absolute():
        raise ValueError("GUI 输出路径必须使用相对路径")
    resolved = (PROJECT_ROOT / path).resolve()
    try:
        resolved.relative_to(PROJECT_ROOT)
    except ValueError as error:
        raise ValueError("GUI 输出路径不能超出项目目录") from error
    return resolved


def _display_path(path):
    """项目内路径显示为相对路径，用户选择的外部路径显示为绝对路径。"""
    path = Path(path).resolve()
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path)


def _available_locales():
    """读取外部语言文件，供界面动态生成语言列表。"""
    locales = []
    if not LOCALE_ROOT.is_dir():
        return locales
    for path in sorted(LOCALE_ROOT.glob("*.json")):
        code = path.stem
        if not re.fullmatch(r"[A-Za-z0-9-]+", code):
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        name = data.get("language.name", code) if isinstance(data, dict) else code
        locales.append({"code": code, "name": str(name)})
    return locales


def _output_setting_key(kind, animation):
    key = f"{kind}_{'animation' if animation else 'static'}"
    if key not in OUTPUT_SETTING_KEYS:
        raise ValueError("未知输出类型")
    return key


def _load_output_settings():
    with _settings_lock:
        if not SETTINGS_PATH.is_file():
            return {}
        try:
            data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        if not isinstance(data, dict):
            return {}
        settings = {
            key: value
            for key, value in data.items()
            if key in OUTPUT_SETTING_KEYS and isinstance(value, str) and value
        }
        # 兼容旧版静态模式保存的完整 PNG 路径；新版统一保存输出目录。
        for key, value in tuple(settings.items()):
            if key.endswith("_static") and Path(value).suffix.lower() == ".png":
                settings[key] = str(Path(value).parent)
        return settings


def _save_output_settings(settings):
    filtered = {
        key: value
        for key, value in settings.items()
        if key in OUTPUT_SETTING_KEYS and isinstance(value, str) and value
    }
    with _settings_lock:
        temporary = SETTINGS_PATH.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(filtered, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporary.replace(SETTINGS_PATH)


def _saved_output_path(kind, animation):
    key = _output_setting_key(kind, animation)
    value = _load_output_settings().get(key)
    return Path(value) if value else None


def _payload_output_path(payload, kind, animation):
    if payload.get("use_saved_output", False):
        path = _saved_output_path(kind, animation)
        if path is None:
            raise ValueError("尚未选择自定义输出路径")
        return path
    return _optional_relative_path(payload.get("output_path"))


def _apply_edition_limits(payload, endpoint, edition):
    """在服务端强制执行发行版本的功能边界。"""
    if edition != EDITION_SIMPLE:
        return payload

    payload = dict(payload)
    if payload.get("animation", False):
        raise ValueError("简易版不支持动画生成")
    if endpoint.endswith("/planet") and payload.get("tone") == "custom":
        raise ValueError("简易版不支持自定义星球风格")
    if endpoint.endswith("/galaxy") and payload.get("theme_name") == "custom":
        raise ValueError("简易版不支持自定义银河风格")

    seed = payload.get("seed")
    if seed is None:
        payload["seed"] = secrets.choice(SIMPLE_SEEDS)
    elif not isinstance(seed, int) or isinstance(seed, bool) or seed not in SIMPLE_SEEDS:
        raise ValueError("简易版 seed 必须在 0-49 之间")
    payload["animation"] = False
    payload["ensure_unique"] = False
    return payload


def _run_native_output_dialog(kind, animation):
    """在 GUI 主线程中打开系统选择器并保存选择结果。"""
    from tkinter import Tk, filedialog

    key = _output_setting_key(kind, animation)
    settings = _load_output_settings()
    current = Path(settings[key]) if key in settings else None
    initial_dir = current
    if initial_dir is None or not initial_dir.is_dir():
        initial_dir = PROJECT_ROOT

    root = Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    root.update()
    try:
        selected = filedialog.askdirectory(
            parent=root,
            initialdir=str(initial_dir),
            mustexist=True,
        )
    finally:
        root.destroy()

    if not selected:
        return None
    selected = str(Path(selected).resolve())
    settings[key] = selected
    _save_output_settings(settings)
    return selected


def _select_native_output(kind, animation):
    """将系统选择器调用转交给运行 GUI 事件循环的主线程。"""
    _output_setting_key(kind, animation)
    if _native_dialog_owner_thread in (None, get_ident()):
        return _run_native_output_dialog(kind, animation)

    completed = Event()
    request = {
        "kind": kind,
        "animation": animation,
        "completed": completed,
        "result": None,
        "error": None,
    }
    _native_dialog_requests.put(request)
    completed.wait()
    if request["error"] is not None:
        raise request["error"]
    return request["result"]


def _process_native_dialog_request(timeout=0.1):
    """处理一个待显示的原生文件对话框。"""
    try:
        request = _native_dialog_requests.get(timeout=timeout)
    except Empty:
        return False
    try:
        request["result"] = _run_native_output_dialog(
            request["kind"], request["animation"]
        )
    except Exception as error:
        request["error"] = error
    finally:
        request["completed"].set()
        _native_dialog_requests.task_done()
    return True


def _reset_saved_output(kind, animation):
    key = _output_setting_key(kind, animation)
    settings = _load_output_settings()
    settings.pop(key, None)
    _save_output_settings(settings)


def _register_preview(path):
    path = Path(path).resolve(strict=True)
    token = secrets.token_urlsafe(18)
    with _preview_lock:
        _preview_files[token] = path
        _preview_files.move_to_end(token)
        while len(_preview_files) > MAX_PREVIEW_FILES:
            _preview_files.popitem(last=False)
    return f"/api/files/{token}"


def _result_payload(paths, seed, **metadata):
    paths = [Path(path).resolve() for path in paths]
    preview_urls = [_register_preview(path) for path in paths]
    return {
        "ok": True,
        "seed": seed,
        "preview_url": preview_urls[0],
        "frame_urls": preview_urls,
        "frame_count": len(paths),
        "output": _display_path(
            paths[0] if len(paths) == 1 else paths[0].parent
        ),
        **metadata,
    }


def _planet_parameters(payload):
    custom_palette = payload.get("custom_palette") if payload.get("tone") == "custom" else None
    tone = "earth" if custom_palette is not None else payload.get("tone", "earth")
    return {
        "size": payload.get("size", 96),
        "tone": tone,
        "seed": payload.get("seed"),
        "ring": payload.get("ring", False),
        "ring_color": payload.get("ring_color"),
        "ring_tilt": payload.get("ring_tilt", 0.42),
        "ring_width": payload.get("ring_width", 0.28),
        "frame": payload.get("frame", False),
        "frame_color": payload.get("frame_color", "#00FFFF"),
        "frame_size": payload.get("frame_size", 12),
        "frame_thickness": payload.get("frame_thickness", 2),
        "frame_padding": payload.get("frame_padding", 4),
        "scale": payload.get("scale", 4),
        "custom_palette": custom_palette,
        "ensure_unique": payload.get("ensure_unique", False),
    }


def generate_planet_from_payload(payload):
    parameters = _planet_parameters(payload)
    animation = payload.get("animation", False)
    output_path = _payload_output_path(payload, "planet", animation)
    if animation:
        seed, paths = generate_animation(
            **parameters,
            frames=payload.get("frames", 24),
            output_dir=output_path,
            filename_prefix=_optional_text(payload.get("filename_prefix")),
        )
        return _result_payload(paths, seed, kind="planet_animation")

    seed = make_planet(**parameters, output_dir=output_path)
    style = "custom" if parameters["custom_palette"] is not None else parameters["tone"]
    path = resolve_static_output_path("planet", style, seed, output_dir=output_path)
    return _result_payload([path], seed, kind="planet")


def _galaxy_parameters(payload):
    custom_theme = payload.get("custom_theme") if payload.get("theme_name") == "custom" else None
    theme_name = None if custom_theme is not None else payload.get("theme_name", "deep_blue")
    return {
        "width": payload.get("width", 800),
        "height": payload.get("height", 450),
        "pixel_size": payload.get("pixel_size", 3),
        "theme_name": theme_name,
        "seamless_axis": payload.get("seamless_axis"),
        "flash_stars": payload.get("flash_stars", 15),
        "seed": payload.get("seed"),
        "custom_theme": custom_theme,
        "ensure_unique": payload.get("ensure_unique", False),
    }


def generate_galaxy_from_payload(payload):
    parameters = _galaxy_parameters(payload)
    animation = payload.get("animation", False)
    output_path = _payload_output_path(payload, "galaxy", animation)
    if animation:
        paths, theme, flash_count, seed = generate_galaxy_animation(
            **parameters,
            frames=payload.get("frames", 24),
            output_dir=output_path,
            filename_prefix=_optional_text(payload.get("filename_prefix")),
        )
        return _result_payload(
            paths,
            seed,
            kind="galaxy_animation",
            theme=theme,
            flash_stars=flash_count,
        )

    path, theme, flash_count, seed = generate_pixel_galaxy(
        **parameters,
        output_dir=output_path,
    )
    return _result_payload(
        [path], seed, kind="galaxy", theme=theme, flash_stars=flash_count
    )


class GeneratorRequestHandler(BaseHTTPRequestHandler):
    server_version = "PixelPlanetGUI/1.0"

    def _send_bytes(
        self,
        content,
        content_type,
        status=HTTPStatus.OK,
        cache_control="no-store",
    ):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", cache_control)
        self.end_headers()
        self.wfile.write(content)

    def _send_json(self, payload, status=HTTPStatus.OK):
        content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send_bytes(content, "application/json; charset=utf-8", status)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path in ("/", "/ui_prototype.html"):
            self._send_bytes(UI_PATH.read_bytes(), "text/html; charset=utf-8")
            return
        if path.startswith("/locales/"):
            locale_name = path.removeprefix("/locales/")
            if re.fullmatch(r"[A-Za-z0-9-]+\.json", locale_name):
                locale_path = LOCALE_ROOT / locale_name
                if locale_path.is_file():
                    self._send_bytes(
                        locale_path.read_bytes(), "application/json; charset=utf-8"
                    )
                    return
        if path == "/api/health":
            edition = getattr(self.server, "edition", EDITION_FULL)
            self._send_json(
                {
                    "ok": True,
                    "edition": edition,
                    "simple_seed_count": len(SIMPLE_SEEDS),
                }
            )
            return
        if path == "/api/settings":
            self._send_json({"ok": True, "outputs": _load_output_settings()})
            return
        if path == "/api/locales":
            self._send_json({"ok": True, "locales": _available_locales()})
            return
        if path.startswith("/api/files/"):
            token = path.removeprefix("/api/files/")
            with _preview_lock:
                file_path = _preview_files.get(token)
            if file_path is not None and file_path.is_file():
                self._send_bytes(
                    file_path.read_bytes(),
                    "image/png",
                    cache_control="private, max-age=3600",
                )
                return
        self._send_json({"ok": False, "error": "资源不存在"}, HTTPStatus.NOT_FOUND)

    def do_POST(self):
        path = urlsplit(self.path).path
        if path not in (
            "/api/generate/planet",
            "/api/generate/galaxy",
            "/api/select-output",
            "/api/reset-output",
        ):
            self._send_json({"ok": False, "error": "接口不存在"}, HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > MAX_REQUEST_BYTES:
                raise ValueError("请求内容为空或过大")
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError("请求必须是 JSON 对象")
            if path == "/api/select-output":
                kind = payload.get("kind")
                animation = bool(payload.get("animation", False))
                selected = _select_native_output(kind, animation)
                self._send_json(
                    {
                        "ok": True,
                        "cancelled": selected is None,
                        "path": selected,
                        "outputs": _load_output_settings(),
                    }
                )
                return
            if path == "/api/reset-output":
                _reset_saved_output(
                    payload.get("kind"), bool(payload.get("animation", False))
                )
                self._send_json(
                    {"ok": True, "outputs": _load_output_settings()}
                )
                return
            payload = _apply_edition_limits(
                payload,
                path,
                getattr(self.server, "edition", EDITION_FULL),
            )
            if path.endswith("/planet"):
                result = generate_planet_from_payload(payload)
            else:
                result = generate_galaxy_from_payload(payload)
            self._send_json(result)
        except (ValueError, TypeError, OSError, json.JSONDecodeError) as error:
            self._send_json(
                {"ok": False, "error": str(error)}, HTTPStatus.BAD_REQUEST
            )
        except Exception as error:
            print(f"生成失败: {error}")
            self._send_json(
                {"ok": False, "error": "生成失败，请查看服务端日志"},
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format % args}")


def run_server(
    host="127.0.0.1",
    port=8765,
    open_browser=True,
    edition=EDITION_FULL,
):
    global _native_dialog_owner_thread

    if edition not in (EDITION_FULL, EDITION_SIMPLE):
        raise ValueError("未知发行版本")
    os.chdir(PROJECT_ROOT)
    try:
        server = ThreadingHTTPServer((host, port), GeneratorRequestHandler)
    except OSError:
        if port == 0:
            raise
        server = ThreadingHTTPServer((host, 0), GeneratorRequestHandler)
    server.edition = edition
    server_thread = Thread(target=server.serve_forever, daemon=True)
    url = f"http://{host}:{server.server_port}/"
    print(f"Pixel Planet Generator GUI: {url}")
    print("按 Ctrl+C 停止服务")
    _native_dialog_owner_thread = get_ident()
    server_thread.start()
    if open_browser:
        webbrowser.open(url)
    try:
        while server_thread.is_alive():
            _process_native_dialog_request()
    except KeyboardInterrupt:
        print("\n服务已停止")
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=2)
        _native_dialog_owner_thread = None


if __name__ == "__main__":
    parser = ArgumentParser(description="启动 Pixel Planet Generator 图形界面")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument(
        "--edition", choices=(EDITION_FULL, EDITION_SIMPLE), default=EDITION_FULL
    )
    args = parser.parse_args()
    run_server(args.host, args.port, not args.no_browser, args.edition)
