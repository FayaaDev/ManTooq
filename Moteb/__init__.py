"""Generate Moteb narration with different seeds."""

import argparse
import os
import secrets
import uuid

from dotenv import load_dotenv

from app.arabic_tts import ROOT, speak


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", help="Seeds between 0 and 4294967295 (default: three random seeds)")
    args = parser.parse_args()
    seeds = args.seeds if args.seeds is not None else [secrets.randbelow(2**32) for _ in range(3)]
    if any(not 0 <= seed < 2**32 for seed in seeds):
        parser.error("Seeds must be between 0 and 4294967295.")
    load_dotenv(ROOT / ".env")
    folder = ROOT / "Moteb"
    try:
        text = (folder / "takes_packed.md").read_text(encoding="utf-8")
        for seed in seeds:
            audio = speak(text, "s8AtpE08HrPmTUNmxgfQ", os.getenv("ELEVENLABS_API_KEY", ""), seed)
            output = folder / f"moteb-seed-{seed}-{uuid.uuid4().hex}.mp3"
            output.write_bytes(audio)
            print(f"Saved audio to {output}")
    except (OSError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
