import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import VoiceClone


class VoiceCloneTest(unittest.TestCase):
    def test_shortcut_reads_script_and_saves_unique_audio(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / "VoiceClone"
            folder.mkdir()
            (folder / "takes_packed.md").write_text("sample narration")
            with patch.object(VoiceClone, "ROOT", root), patch.object(
                VoiceClone, "speak", return_value=b"audio"
            ) as speak, patch.object(VoiceClone, "load_dotenv"), patch.dict(
                VoiceClone.os.environ, {"ELEVENLABS_API_KEY": "test-key"}
            ):
                VoiceClone.main()
                VoiceClone.main()
            speak.assert_called_with("sample narration", "ptiQIMgSFdkKSzpiK3Vu", "test-key", 1729462083)
            outputs = list(folder.glob("*.mp3"))
            self.assertEqual(len(outputs), 2)
            self.assertTrue(all(output.read_bytes() == b"audio" for output in outputs))

    def test_missing_script_exits_without_calling_provider(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(
            VoiceClone, "ROOT", Path(directory)
        ), patch.object(VoiceClone, "load_dotenv"), patch.object(VoiceClone, "speak") as speak:
            with self.assertRaises(SystemExit):
                VoiceClone.main()
            speak.assert_not_called()
