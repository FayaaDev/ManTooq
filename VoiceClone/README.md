# VoiceClone

1. Edit `VoiceClone/takes_packed.md`.
2. Set `ELEVENLABS_API_KEY` in the project's `.env`.
3. From the project root, run:

```bash
uv run clone
```

MP3 files are saved in `VoiceClone/`. Each run uses paid ElevenLabs generation.


uv run python app/arabic_tts.py speak \
  "$(<VoiceClone/takes_packed.md)" \
  --voice-id 'ptiQIMgSFdkKSzpiK3Vu' \
  --seed 1729462083 \
  --output "VoiceClone/takes-v4-turbo-$(uuidgen).mp3"
