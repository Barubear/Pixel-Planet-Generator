# Pixel Art Planet Generator — pure web edition

This is the standalone generator, with no portfolio home page or dependency on Barubear Dreamer. Deploy this directory as the site root. The separate portfolio project is maintained outside this repository.

This edition runs entirely in the browser. It does not call the Python application, a local API, or a remote image-generation service.

## Run locally

On Windows, double-click `启动网页版.cmd`. You can also open `index.html` directly in a current browser.

No installation or build step is required. A current version of Chrome or Edge is recommended, especially for the optional existing-seed folder scan.

## Included features

- Static planet PNG generation
- Looping planet PNG-frame animation (15–60 frames)
- Static galaxy PNG generation
- Looping galaxy PNG-frame animation (15–60 frames)
- Built-in planet styles and galaxy themes
- Planet ocean coverage from 30% to 90% in 10% steps
- Galaxy star amount from 30% to 90% in 10% steps
- Galaxy sizes up to 1024×1024
- Fully random seeds by default, with reproducible or session-unique input modes
- One seed per generation: Reproduce uses only the first value; comma-separated values in Avoid duplicates form an exclusion list
- Optional existing-seed scan from a user-approved local folder in Avoid duplicates mode
- Custom colors and deterministic browser seeds
- Horizontal, vertical, or two-axis edge wrapping; ordinary stars twinkle in fixed positions during animation
- Optional central galaxy spiral, disabled by default; when enabled it rotates independently during animation
- Optional corner-frame button-state variants: random and duplicate-avoidance generation includes plain, hover, pressed, and disabled sets; seed reproduction includes the three framed sets
- Built-in Chinese and English UI with editable local translation files
- A friendly Chinese and English guide page
- Browser downloads for all generated images and ZIP files

Single static results download as PNG files named:

```text
<style>-<seed>.png
<theme>-<seed>.png
```

Animations use numbered files such as `frame000.png` and download as ZIP files. Multiple generated results are also packed into one ZIP file. The final download location is controlled by the browser.

## Compatibility note

The web and current desktop interfaces share a renderer and reproduce the same content with matching seeds and settings. Legacy Python/Pillow script APIs use a separate algorithm and are not pixel-identical.

The optional seed-scan folder picker is a browser capability and may require a secure context. Its selected handle is kept only for the current page session. If it is unavailable, image generation and downloads still work.

Reproduce uses only the first entered seed and shows an alert if it is empty. Avoid duplicates uses the comma-separated input as an exclusion list, also excluding seeds already generated for the same generator on this page. Refreshing clears this history; seeds are not stored in cookies. Fully random mode does not guarantee uniqueness.

Optional folder lookup replaces the input with an editable list after the user chooses a folder and grants read access; no directory is preset. It scans names recursively, recognizing examples such as `earth-123.png` and `galaxy_animation-deep_blue-123.zip`. It does not read ZIP contents or recognize current button-state filenames; add those seeds manually.

Browsers may refuse access to a system-managed or security-sensitive directory. If Downloads itself cannot be selected, create a regular subfolder such as `Downloads/PixelPlanetOutput` and select that subfolder. The scanner skips individual unreadable subdirectories when the selected root remains accessible.

Complete built-in translations live in `js/locales.js` so direct `file://` startup works. Editable JSON reference files are in `locales/`.

The folder is also ready for static deployment: upload its contents to any static host. No backend environment variables or server-side dependencies are required.
