# Project guide

This is a local Arabic text-to-speech and voice-cloning app. Keep changes small and preserve both the Streamlit UI (`app/app.py`) and CLI (`app/arabic_tts.py`). Unit tests are in `tests/unit/`, browser tests in `tests/e2e/`, and product notes in `docs/`.

- Run with `uv sync` and `uv run python -m streamlit run app/app.py` (Python 3.13+).
- Test with `uv run python -m unittest -v`; browser tests need `uv run python -m playwright install chromium`. Do not make real ElevenLabs requests in tests.
- Keep the UI Arabic, RTL, and named «استوديو الصوت العربي». Preserve the bundled Thmanyah font. API keys and voice IDs should read left-to-right.
- Use `streamlit-shadcn-ui` V2 for its existing controls. Its trigger buttons cannot go inside `st.form`; its Shadow DOM hosts need RTL and a matching Streamlit theme. Keep native Streamlit upload, audio, and download controls where needed.
- Keep the entered API key in the Streamlit session; `.env` or `ELEVENLABS_API_KEY` can supply it locally. Never log, display, commit, or persist keys from the UI.
- `app/arabic_tts.py` owns API calls, validation, the default speech seed, and the locally saved cloned voice ID at `.local/voice_id`. UI changes should call these functions rather than duplicate their logic.
- Local voice storage is shared by sessions on the same installation; do not describe it as per-user storage in a multi-user deployment.
