# منطوق — ManTooq

Arabic text-to-speech and voice cloning.

## Voice generation

Edit `VoiceClone/takes_packed.md`, then run from this project directory:

```bash
uv run clone
```

This uses Eleven v4 Turbo, voice `ptiQIMgSFdkKSzpiK3Vu`, and seed
`1729462083`. Each run makes a paid ElevenLabs request and saves a uniquely
named MP3 in `VoiceClone/`. Set `ELEVENLABS_API_KEY` in your environment or
local `.env`; never commit your key.

## App and existing CLI

```bash
uv run python -m streamlit run app/app.py
uv run python app/arabic_tts.py --help
```
