# Moteb

Voice ID: `s8AtpE08HrPmTUNmxgfQ`

1. Edit `Moteb/takes_packed.md`.
2. Set `ELEVENLABS_API_KEY` in the project's `.env` or environment.
3. From this folder or the project root, run:

```bash
uv run moteb
```

Generates three MP3s with random seeds using the app's speech settings.
Moteb uses `eleven_v4_turbo`, stability `0.5`, and similarity `0.75`. Other voices keep their existing settings.
To choose seeds:

```bash
uv run moteb --seeds 42 1729462083 2752657480
```

MP3s are saved in `Moteb/`, with the seed and a unique suffix in each filename.
Each seed makes a paid ElevenLabs request. Existing recordings are not overwritten.
Seeds provide best-effort reproducibility, not guaranteed identical audio.
