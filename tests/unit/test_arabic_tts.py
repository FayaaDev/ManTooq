import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import arabic_tts


class VoiceFlowTest(unittest.TestCase):
    def test_existing_clone_id_is_migrated(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(
            arabic_tts, "ROOT", Path(folder)
        ), patch.object(arabic_tts, "VOICE_FILE", Path(folder) / ".local" / "voice_id"):
            (Path(folder) / "cloned_voice_id.txt").write_text("old-voice-id\n")
            self.assertEqual(arabic_tts.default_voice_id(), "old-voice-id")
            self.assertEqual(arabic_tts.VOICE_FILE.read_text(), "old-voice-id\n")

    def test_clone_becomes_default_and_library_voice_overrides_it(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(
            arabic_tts, "VOICE_FILE", Path(folder) / ".local" / "voice_id"
        ), patch.object(arabic_tts, "ROOT", Path(folder)), patch.object(
            arabic_tts, "ElevenLabs"
        ) as client:
            client.return_value.voices.ivc.create.return_value.voice_id = "cloned-id"
            client.return_value.text_to_speech.convert.return_value = [b"arabic", b" audio"]

            self.assertEqual(arabic_tts.clone_voice(b"sample", "sample.wav", "My voice", "key"), "cloned-id")
            self.assertEqual(arabic_tts.default_voice_id(), "cloned-id")
            self.assertEqual(arabic_tts.speak("مرحبا", "library-id", "key"), b"arabic audio")
            self.assertEqual(client.return_value.text_to_speech.convert.call_args.kwargs["voice_id"], "library-id")

    def test_missing_voice_and_key_do_not_call_api(self):
        with patch.object(arabic_tts, "ElevenLabs") as client:
            with self.assertRaises(ValueError):
                arabic_tts.speak("مرحبا", "", "key")
            with self.assertRaises(ValueError):
                arabic_tts.clone_voice(b"sample", "sample.wav", "My voice", "")
            client.assert_not_called()


if __name__ == "__main__":
    unittest.main()
