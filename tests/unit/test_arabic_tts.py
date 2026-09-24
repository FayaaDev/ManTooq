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
            self.assertEqual(client.return_value.text_to_speech.convert.call_args.kwargs["seed"], arabic_tts.DEFAULT_SEED)

    def test_saved_seeds_are_reusable(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(
            arabic_tts, "SEED_FILE", Path(folder) / ".local" / "seeds.json"
        ):
            arabic_tts.save_seed(1)
            arabic_tts.save_seed(2)
            arabic_tts.save_seed(1)
            self.assertEqual(arabic_tts.saved_seeds(), [arabic_tts.DEFAULT_SEED, 1, 2])

    def test_generated_audio_is_saved_with_its_seed(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(
            arabic_tts, "GENERATED_AUDIO_DIR", Path(folder) / "generated_audio"
        ):
            first = arabic_tts.save_generated_audio(b"first", 123)
            second = arabic_tts.save_generated_audio(b"second", 123)
            self.assertNotEqual(first, second)
            self.assertEqual(first.read_bytes(), b"first")
            self.assertEqual(second.read_bytes(), b"second")
            self.assertEqual({(path, seed) for path, seed in arabic_tts.saved_generated_audio()},
                             {(first, 123), (second, 123)})

    def test_missing_voice_and_key_do_not_call_api(self):
        with patch.object(arabic_tts, "ElevenLabs") as client:
            with self.assertRaises(ValueError):
                arabic_tts.speak("مرحبا", "", "key")
            with self.assertRaises(ValueError):
                arabic_tts.clone_voice(b"sample", "sample.wav", "My voice", "")
            client.assert_not_called()


if __name__ == "__main__":
    unittest.main()
