"""简易版 Windows 发布入口。"""

from gui_server import EDITION_SIMPLE, run_server


if __name__ == "__main__":
    run_server(port=18766, open_browser=True, edition=EDITION_SIMPLE)
