import os
from pathlib import Path
import tempfile
import unittest

from PIL import Image

import gui_server


class FrameVariantGenerationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.previous_root = gui_server.PROJECT_ROOT
        self.previous_cwd = Path.cwd()
        gui_server.PROJECT_ROOT = self.root
        os.chdir(self.root)

    def tearDown(self):
        os.chdir(self.previous_cwd)
        gui_server.PROJECT_ROOT = self.previous_root
        with gui_server._preview_lock:
            gui_server._preview_files.clear()
        self.temporary.cleanup()

    @staticmethod
    def _payload(**overrides):
        payload = {
            "tone": "earth",
            "size": 32,
            "scale": 1,
            "seed": None,
            "seed_reproduce": False,
            "ensure_unique": True,
            "ring": False,
            "frame": True,
            "frame_variants": True,
            "frame_color": "#00FFFF",
            "frame_pressed_color": "#008383",
            "frame_disabled_color": "#808080",
            "frame_size": 8,
            "frame_thickness": 1,
            "frame_padding": 2,
            "animation": False,
            "output_path": "output-test",
        }
        payload.update(overrides)
        return payload

    def test_random_or_unique_seed_generates_plain_and_three_frame_states(self):
        result = gui_server.generate_planet_from_payload(self._payload())

        self.assertEqual(result["variant_count"], 4)
        self.assertEqual(result["frame_count"], 1)
        folder = self.root / "output-test"
        files = {path.stem.rsplit("-", 1)[-1]: path for path in folder.glob("*.png")}
        self.assertEqual(set(files), {"plain", "hover", "pressed", "disabled"})
        expected = {
            "plain": (0, 0, 0, 0),
            "hover": (0, 255, 255, 255),
            "pressed": (0, 131, 131, 255),
            "disabled": (128, 128, 128, 255),
        }
        for state, color in expected.items():
            with Image.open(files[state]) as image:
                self.assertEqual(image.getpixel((2, 2)), color)

    def test_reproduced_seed_generates_only_three_framed_states(self):
        result = gui_server.generate_planet_from_payload(
            self._payload(seed=42, seed_reproduce=True, ensure_unique=False)
        )

        self.assertEqual(result["variant_count"], 3)
        names = {path.stem.rsplit("-", 1)[-1] for path in (self.root / "output-test").glob("*.png")}
        self.assertEqual(names, {"hover", "pressed", "disabled"})

    def test_animation_uses_one_subdirectory_per_state(self):
        result = gui_server.generate_planet_from_payload(
            self._payload(
                seed=7,
                seed_reproduce=True,
                ensure_unique=False,
                animation=True,
                frames=15,
            )
        )

        self.assertEqual(result["variant_count"], 3)
        self.assertEqual(result["frame_count"], 15)
        folder = self.root / "output-test"
        self.assertEqual({path.name for path in folder.iterdir()}, {"hover", "pressed", "disabled"})
        for state in ("hover", "pressed", "disabled"):
            self.assertEqual(len(list((folder / state).glob("*.png"))), 15)


if __name__ == "__main__":
    unittest.main()
