import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from app import arabic_tts


class AppStateTest(unittest.TestCase):
    def test_connection_and_audio_result_across_reruns(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {"ELEVENLABS_API_KEY": ""}), patch.object(
            arabic_tts, "ROOT", Path(folder)
        ), patch.object(arabic_tts, "VOICE_FILE", Path(folder) / "voice_id"):
            at = AppTest.from_file(str(Path(__file__).resolve().parents[2] / "app" / "app.py")).run()
            self.assertFalse(at.exception)
            self.assertEqual(at.title[0].value, "استوديو الصوت العربي")
            self.assertEqual(len(at.get("audio")), 0)
            self.assertEqual(len(at.get("download_button")), 0)

            at.text_input[0].set_value("test-key").run()
            self.assertFalse(at.exception)
            self.assertEqual(at.text_input[0].value, "test-key")
            self.assertEqual(len(at.get("audio")), 0)

            at.session_state["audio"] = b"ID3\x04\x00\x00\x00\x00\x00\x00"
            at.run()
            self.assertFalse(at.exception)
            self.assertEqual(at.text_input[0].value, "test-key")
            self.assertEqual(len(at.get("audio")), 1)
            self.assertEqual(at.get("download_button")[0].label, "حمّل ملف MP3")


if __name__ == "__main__":
    unittest.main()
