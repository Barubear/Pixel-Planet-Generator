# Pixel Art Planet Generator

像素星球与银河生成器。本仓库只维护桌面版与独立网页版，不再包含 Barubear Dreamer 主站。

## 项目结构

| 目录 | 用途 |
|---|---|
| `web-version/` | 独立网页版，包含生成器、中英文使用说明、常见问题、关于、隐私及许可页面 |
| `desktop-version/` | 桌面启动程序、浏览器界面、保留的 Python 接口、测试与打包脚本 |
| `desktop-version/package/` | 本地 Windows 发行包，不纳入新的 Git 提交 |

原主站已整体迁至相邻的 `../Barubeardreamer/` 独立项目。主站首页及其 `/PixelArtPlanetGenerator/` 子页面在那里维护，不属于本仓库；本仓库的网页版不依赖主站文件，也没有返回主站按钮。

## 使用网页版

双击 `web-version/启动网页版.cmd`，或直接打开 `web-version/index.html`。无需构建即可使用；部署时将 `web-version` 的内容整体放入静态网站目录。

生成与预览在浏览器完成。点击保存按钮后，单张结果下载为 PNG，多图或动画下载为 ZIP，下载位置由浏览器决定。

详见 [网页版 README](web-version/README.md) 和 [中英文使用说明](web-version/guide.html)。

## 使用桌面版

在项目使用的 Conda 环境中运行：

```powershell
Set-Location desktop-version
conda activate torch
pip install -r requirements.txt
python gui_server.py
```

桌面程序在本机提供页面服务，并使用系统默认浏览器打开生成界面。已打包的版本可直接运行发行目录内的 EXE，分发时需保留整个程序目录。

| 功能 | 网页版 / 桌面完整版 | 桌面简易版 |
|---|---|---|
| 静态星球与银河 | 支持 | 支持 |
| 15–60 帧动画 | 支持 | 不支持 |
| 自定义配色 | 支持 | 不支持 |
| Seed 范围 | 0–2147483647 | 0–49，每个风格 50 个 |
| 比例、行星环、角标状态套图、无缝方向 | 支持 | 支持 |
| 中英文、PNG / ZIP 下载 | 支持 | 支持 |

在 `desktop-version` 中运行 `.\build_packages.ps1` 可重新打包。该脚本会清理现有发布目录，请先备份个人语言包和其他文件。详见 [桌面版 README](desktop-version/README.md)。

## 当前功能与规则

- 海洋占比与星星数量占比为 30%–90%，每 10% 一档；银河宽高最大为 1024。
- Seed 默认为随机。复现只读取第一个 Seed；避免重复中的多个逗号分隔值是排除列表，不是批量生成。
- 可在避免重复模式下授权读取本地文件夹，按可识别的文件名查询 Seed；没有预选目录。文件夹权限与识别限制见使用说明。
- 银河无缝方向只控制边缘拼接，普通星星原地闪烁，中心漩涡默认关闭，开启后单独旋转。
- 开启角标边框及变色版本后，随机或避免重复生成无印、悬浮、按下、不可按下四套图；复现只生成三套带角标图。
- 当前桌面界面与网页版共用渲染逻辑；相同 Seed 和参数可复现相同内容。保留的 Python/Pillow 接口是另一套算法，不能保证结果一致。

## 维护与版本管理

独立网页版位于 `web-version`，桌面界面位于 `desktop-version/web_app`；两者是独立文件副本，更新公共功能时需要同步，并保留桌面版的版本限制及外部语言加载逻辑。相邻主站的生成器也是独立副本，不会自动获得本仓库更新。

本地生成结果、缓存、依赖目录和 Windows 发行包保留在磁盘，通过 `.gitignore` 排除。源码、页面、语言文件、文档和打包脚本纳入版本管理。历史提交中的旧发行文件不会从 Git 历史中删除。

软件许可见 [LICENSE](LICENSE)；生成素材的使用条件见 [许可说明](web-version/license.html)。
