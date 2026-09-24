"""Isolated Streamlit entrypoint for browser tests; never use with real credentials."""

import json
import os
import runpy
from pathlib import Path
from types import SimpleNamespace

from app import arabic_tts


arabic_tts.VOICE_FILE = Path(os.environ["E2E_VOICE_FILE"])
arabic_tts.ROOT = arabic_tts.VOICE_FILE.parent.parent


def record(event):
    with open(os.environ["E2E_EVENTS_FILE"], "a") as events:
        events.write(json.dumps(event, ensure_ascii=False) + "\n")


class FakeElevenLabs:
    def __init__(self, api_key):
        self.voices = SimpleNamespace(ivc=SimpleNamespace(create=self.create))
        self.text_to_speech = SimpleNamespace(convert=self.convert)
        self.has_key = bool(api_key)

    def create(self, *, name, files, labels):
        record({"action": "clone", "name": name, "filename": files[0].name, "has_key": self.has_key})
        return SimpleNamespace(voice_id="cloned-e2e-id")

    def convert(self, *, text, voice_id, **kwargs):
        record({"action": "speak", "text": text, "voice_id": voice_id, "has_key": self.has_key})
        if text == "E2E_FAIL":
            raise RuntimeError("Fake API failure")
        return [b"ID3\x04\x00\x00\x00\x00\x00\x00"]


arabic_tts.ElevenLabs = FakeElevenLabs
runpy.run_path(str(Path(__file__).resolve().parents[2] / "app" / "app.py"))
