"""استنسخ صوتًا أو حوّل النص العربي إلى صوت باستخدام ElevenLabs."""

import argparse
import os
from io import BytesIO
from pathlib import Path

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs.types import VoiceSettings


ROOT = Path(__file__).resolve().parent.parent
VOICE_FILE = ROOT / ".local" / "voice_id"
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
    if old_file.exists():
        voice_id = old_file.read_text().strip()
        if voice_id:
            save_voice_id(voice_id)
        return voice_id
    return ""


def save_voice_id(voice_id):
    VOICE_FILE.parent.mkdir(parents=True, exist_ok=True)
    VOICE_FILE.write_text(voice_id + "\n")


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


def speak(text, voice_id, api_key, seed=2752657480):
    if not api_key:
        raise ValueError("أدخل مفتاح ElevenLabs API.")
    if not text.strip():
        raise ValueError("أدخل النص المراد تحويله إلى صوت.")
    if not voice_id.strip():
        raise ValueError("استنسخ صوتًا أو أدخل معرّف صوت من المكتبة.")
    if not 0 <= seed < 2**32:
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
    speech.add_argument("--seed", type=int, default=2752657480)
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
