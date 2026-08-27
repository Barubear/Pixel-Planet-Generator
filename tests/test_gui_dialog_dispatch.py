import tempfile
import unittest
from pathlib import Path
from threading import Thread, get_ident
from types import SimpleNamespace
from unittest.mock import Mock, patch

import gui_server


class NativeDialogDispatchTests(unittest.TestCase):
    def test_simple_edition_limits_seed_and_features(self):
        payload = gui_server._apply_edition_limits(
            {"tone": "earth", "seed": 49, "animation": False},
            "/api/generate/planet",
            gui_server.EDITION_SIMPLE,
        )
        self.assertEqual(payload["seed"], 49)
        self.assertFalse(payload["ensure_unique"])

        for invalid in (
            {"tone": "earth", "seed": 50},
            {"tone": "custom", "seed": 0},
            {"tone": "earth", "seed": 0, "animation": True},
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                gui_server._apply_edition_limits(
                    invalid,
                    "/api/generate/planet",
                    gui_server.EDITION_SIMPLE,
                )

    def test_external_locale_files_are_discovered(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            locale_root = Path(temp_dir)
            (locale_root / "test-LANG.json").write_text(
                '{"language.name": "Test Language"}', encoding="utf-8"
            )
            with patch.object(gui_server, "LOCALE_ROOT", locale_root):
                locales = gui_server._available_locales()

        self.assertEqual(
            locales, [{"code": "test-LANG", "name": "Test Language"}]
        )

    def test_static_mode_uses_directory_picker(self):
        class FakeRoot:
            def withdraw(self):
                pass

            def attributes(self, *_args):
                pass

            def update(self):
                pass

            def destroy(self):
                pass

        with tempfile.TemporaryDirectory() as temp_dir:
            selected_dir = Path(temp_dir) / "selected"
            selected_dir.mkdir()
            dialog = SimpleNamespace(
                askdirectory=Mock(return_value=str(selected_dir))
            )
            tkinter = SimpleNamespace(Tk=FakeRoot, filedialog=dialog)
            settings_path = Path(temp_dir) / "settings.json"

            with patch.dict("sys.modules", {"tkinter": tkinter}), patch.object(
                gui_server, "SETTINGS_PATH", settings_path
            ):
                selected = gui_server._run_native_output_dialog(
                    "planet", False
                )

            self.assertEqual(selected, str(selected_dir.resolve()))
            dialog.askdirectory.assert_called_once()

    def test_request_thread_dispatches_dialog_to_owner_thread(self):
        owner_thread = get_ident()
        results = []
        dialog_threads = []

        def fake_dialog(kind, animation):
            dialog_threads.append(get_ident())
            return f"{kind}:{animation}"

        previous_owner = gui_server._native_dialog_owner_thread
        gui_server._native_dialog_owner_thread = owner_thread
        try:
            with patch.object(
                gui_server, "_run_native_output_dialog", side_effect=fake_dialog
            ):
                worker = Thread(
                    target=lambda: results.append(
                        gui_server._select_native_output("planet", False)
                    )
                )
                worker.start()
                self.assertTrue(
                    gui_server._process_native_dialog_request(timeout=1)
                )
                worker.join(timeout=1)
        finally:
            gui_server._native_dialog_owner_thread = previous_owner

        self.assertFalse(worker.is_alive())
        self.assertEqual(results, ["planet:False"])
        self.assertEqual(dialog_threads, [owner_thread])


if __name__ == "__main__":
    unittest.main()
