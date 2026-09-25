"""استنسخ صوتًا أو حوّل النص العربي إلى صوت باستخدام ElevenLabs."""

import argparse
import json
import os
import uuid
from io import BytesIO
from pathlib import Path

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs.types import VoiceSettings


ROOT = Path(__file__).resolve().parent.parent
# Tauri passes its user-writable app-data directory to the bundled Python process.
DATA_DIR = Path(os.environ["MANTOOQ_DATA_DIR"]).expanduser() if os.getenv("MANTOOQ_DATA_DIR") else ROOT / ".local"
VOICE_FILE = DATA_DIR / "voice_id"
SEED_FILE = DATA_DIR / "seeds.json"
GENERATED_AUDIO_DIR = DATA_DIR / "generated_audio"
DEFAULT_SEED = 2752657480
VOICE_SETTINGS = VoiceSettings(
    stability=0.7,
    similarity_boost=0.9,
    use_speaker_boost=True,
    style=0.0,
    speed=0.95,
)


def default_voice_id():
    if VOICE_FILE.exists():
        return VOICE_FILE.read_text().strip()

    # Keep existing local clones usable when upgrading from the original scripts.
    old_file = ROOT / "cloned_voice_id.txt"
    if not os.getenv("MANTOOQ_DATA_DIR") and old_file.exists():
        voice_id = old_file.read_text().strip()
        if voice_id:
            save_voice_id(voice_id)
        return voice_id
    return ""


def save_voice_id(voice_id):
    VOICE_FILE.parent.mkdir(parents=True, exist_ok=True)
    VOICE_FILE.write_text(voice_id + "\n")


def saved_seeds():
    try:
        seeds = json.loads(SEED_FILE.read_text())
    except (OSError, json.JSONDecodeError):
        seeds = []
    return list(dict.fromkeys([DEFAULT_SEED, *(seed for seed in seeds if type(seed) is int and 0 <= seed < 2**32)]))


def save_seed(seed):
    if type(seed) is not int or not 0 <= seed < 2**32:
        raise ValueError("يجب أن تكون قيمة seed بين 0 و4294967295.")
    # ponytail: retain 20 recent seeds; use a database only if shared history needs to grow.
    seeds = [seed, *(saved_seed for saved_seed in saved_seeds() if saved_seed != seed)][:20]
    SEED_FILE.parent.mkdir(parents=True, exist_ok=True)
    SEED_FILE.write_text(json.dumps(seeds) + "\n")


def save_generated_audio(audio, seed):
    GENERATED_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    path = GENERATED_AUDIO_DIR / f"{seed}-{uuid.uuid4().hex}.mp3"
    path.write_bytes(audio)
    return path


def saved_generated_audio():
    return [(path, int(path.stem.split("-", 1)[0])) for path in sorted(
        GENERATED_AUDIO_DIR.glob("[0-9]*-*.mp3"), key=lambda path: path.stat().st_mtime_ns, reverse=True
    )]


def clone_voice(sample, filename, name, api_key):
    if not api_key:
        raise ValueError("أدخل مفتاح ElevenLabs API.")
    if not sample:
        raise ValueError("ارفع تسجيلًا صوتيًا غير فارغ.")
    if not name.strip():
        raise ValueError("أدخل اسمًا للصوت.")

    audio = BytesIO(sample)
    audio.name = filename
    voice = ElevenLabs(api_key=api_key).voices.ivc.create(
        name=name.strip(), files=[audio], labels={}
    )
    save_voice_id(voice.voice_id)
    return voice.voice_id


def speak(text, voice_id, api_key, seed=DEFAULT_SEED):
    if not api_key:
        raise ValueError("أدخل مفتاح ElevenLabs API.")
    if not text.strip():
        raise ValueError("أدخل النص المراد تحويله إلى صوت.")
    if not voice_id.strip():
        raise ValueError("استنسخ صوتًا أو أدخل معرّف صوت من المكتبة.")
    if type(seed) is not int or not 0 <= seed < 2**32:
        raise ValueError("يجب أن تكون قيمة seed بين 0 و4294967295.")

    return b"".join(
        ElevenLabs(api_key=api_key).text_to_speech.convert(
            text=text.strip(),
            voice_id=voice_id.strip(),
            model_id="eleven_v3",
            output_format="mp3_44100_128",
            voice_settings=VOICE_SETTINGS,
            seed=seed,
        )
    )


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    clone = commands.add_parser("clone", help="استنسخ صوتًا من تسجيل")
    clone.add_argument("--sample", type=Path, required=True)
    clone.add_argument("--name", required=True)
    speech = commands.add_parser("speak", help="حوّل النص العربي إلى صوت")
    speech.add_argument("text")
    speech.add_argument("--voice-id", help="استخدم صوتًا آخر بدل الصوت المحفوظ")
    speech.add_argument("--output", type=Path, default=ROOT / "output" / "speech.mp3")
    speech.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()

    try:
        api_key = os.getenv("ELEVENLABS_API_KEY", "")
        if args.command == "clone":
            if not args.sample.is_file():
                parser.error(f"لم يُعثر على التسجيل الصوتي: {args.sample}")
            voice_id = clone_voice(args.sample.read_bytes(), args.sample.name, args.name, api_key)
            print(f"استنسخت الصوت وحفظته للاستخدام تلقائيًا: {voice_id}")
        else:
            audio = speak(args.text, args.voice_id or default_voice_id(), api_key, args.seed)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_bytes(audio)
            print(f"حُفظ الملف في {args.output}")
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
