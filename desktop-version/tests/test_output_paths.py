import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import output_paths


class OutputPathTests(unittest.TestCase):
    def test_static_default_path_is_separated_by_kind(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with patch.object(output_paths, "OUTPUT_ROOT", root):
                path = output_paths.resolve_static_output_path("planet", "earth", 42)

            self.assertEqual(path, root / "planet" / "earth-42" / "earth-42.png")
            self.assertTrue(path.parent.is_dir())

    def test_static_custom_file_path_takes_priority(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            requested = Path(temp_dir) / "custom" / "planet.png"
            path = output_paths.resolve_static_output_path("planet", "earth", 42, requested)

            self.assertEqual(path, requested)
            self.assertTrue(requested.parent.is_dir())

    def test_static_custom_directory_appends_generated_filename(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            requested_dir = Path(temp_dir) / "images"
            path = output_paths.resolve_static_output_path(
                "planet", "earth", 42, output_dir=requested_dir
            )

            self.assertEqual(path, requested_dir / "earth-42.png")
            self.assertTrue(requested_dir.is_dir())

    def test_animation_default_path_uses_own_kind_and_padded_index(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with patch.object(output_paths, "OUTPUT_ROOT", root):
                path = output_paths.resolve_animation_frame_path(
                    "galaxy_animation", "deep_blue", 7, 2
                )

            self.assertEqual(
                path,
                root
                / "galaxy_animation"
                / "deep_blue-7"
                / "deep_blue-7-frame002.png",
            )

    def test_animation_custom_dir_and_prefix_take_priority(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            requested_dir = Path(temp_dir) / "frames"
            path = output_paths.resolve_animation_frame_path(
                "planet_animation",
                "earth",
                42,
                12,
                output_dir=requested_dir,
                filename_prefix="spin/demo",
            )

            self.assertEqual(path, requested_dir / "spin_demo-frame012.png")
            self.assertTrue(requested_dir.is_dir())


if __name__ == "__main__":
    unittest.main()
