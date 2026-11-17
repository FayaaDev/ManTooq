import tempfile
import unittest
from pathlib import Path
from unittest.mock import call, patch

import Moteb


class MotebTest(unittest.TestCase):
    def test_generates_each_seed_without_overwriting(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / "Moteb"
            folder.mkdir()
            (folder / "takes_packed.md").write_text("sample narration")
            with patch.object(Moteb, "ROOT", root), patch.object(
                Moteb, "speak", return_value=b"audio"
            ) as speak, patch.object(Moteb, "load_dotenv"), patch.dict(
                Moteb.os.environ, {"ELEVENLABS_API_KEY": "test-key"}
            ), patch("sys.argv", ["moteb", "--seeds", "0", "4294967295"]):
                Moteb.main()
                Moteb.main()
            self.assertEqual(speak.call_args_list, [
                call("sample narration", "s8AtpE08HrPmTUNmxgfQ", "test-key", seed)
                for seed in [0, 4294967295, 0, 4294967295]
            ])
            outputs = list(folder.glob("moteb-seed-*.mp3"))
            self.assertEqual(len(outputs), 4)
            self.assertTrue(all(output.read_bytes() == b"audio" for output in outputs))

    def test_default_generates_three_random_seeds(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / "Moteb"
            folder.mkdir()
            (folder / "takes_packed.md").write_text("sample narration")
            with patch.object(Moteb, "ROOT", root), patch.object(
                Moteb, "speak", return_value=b"audio"
            ) as speak, patch.object(Moteb, "load_dotenv"), patch.object(
                Moteb.secrets, "randbelow", side_effect=[12, 34, 56]
            ), patch("sys.argv", ["moteb"]):
                Moteb.main()
            self.assertEqual([entry.args[3] for entry in speak.call_args_list], [12, 34, 56])

    def test_invalid_seed_fails_before_generation(self):
        for seed in ["-1", "4294967296"]:
            with self.subTest(seed=seed), patch(
                "sys.argv", ["moteb", "--seeds", seed]
            ), patch.object(Moteb, "speak") as speak:
                with self.assertRaises(SystemExit):
                    Moteb.main()
                speak.assert_not_called()

    def test_missing_script_fails_before_generation(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(
            Moteb, "ROOT", Path(directory)
        ), patch.object(Moteb, "load_dotenv"), patch.object(
            Moteb, "speak"
        ) as speak, patch("sys.argv", ["moteb", "--seeds", "42"]):
            with self.assertRaises(SystemExit):
                Moteb.main()
            speak.assert_not_called()
