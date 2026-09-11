# Pixel Art Planet Generator — desktop browser interface

Images are rendered in the browser. The local Python launcher serves this interface and provides edition settings and external translations.

## Run locally

Start the desktop EXE, or run `python gui_server.py` from the desktop source directory. Use the page opened by the launcher so edition limits and external translations are loaded.

Full includes the features below. Lite disables animation and custom colors and limits seeds to 0–49. See the desktop README or package instructions for setup.

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

Use the separate web edition for static hosting; this desktop interface expects the local launcher for edition configuration and external translations.
