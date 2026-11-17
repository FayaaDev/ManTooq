"""Generate the VoiceClone script with the saved narration settings."""

import os
import uuid

from dotenv import load_dotenv

from app.arabic_tts import ROOT, speak


def main():
    load_dotenv(ROOT / ".env")
    folder = ROOT / "VoiceClone"
    try:
        text = (folder / "takes_packed.md").read_text()
        audio = speak(text, "ptiQIMgSFdkKSzpiK3Vu", os.getenv("ELEVENLABS_API_KEY", ""), 1729462083)
        output = folder / f"takes-v4-turbo-{uuid.uuid4().hex}.mp3"
        output.write_bytes(audio)
    except (OSError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Saved audio to {output}")
