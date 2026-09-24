# Tauri Packaging Plan

## Installable macOS app

**Approach:** Keep Streamlit and the existing Python speech logic. Tauri will provide the desktop window and manage a bundled Python executable that serves the UI on `127.0.0.1`. A DMG should install and launch without requiring the user to install Python or `uv`.

1. **Prove the bundle works.** Package `app/app.py`, `app/arabic_tts.py`, the Thmanyah font, Streamlit configuration, and Python dependencies into a macOS executable. Check that it starts from outside the repository and renders the existing Arabic, RTL interface. Streamlit's dependencies make this the main feasibility check.

2. **Make saved data installation-safe.** `app/arabic_tts.py` currently writes under the repository's `.local/` directory. Give the packaged app a user-writable application-data directory for voice ID, seeds, and MP3s while retaining current paths for source runs and the CLI. Test persistence across restarts; keep API keys out of the bundle and saved data.

3. **Add the Tauri v2 shell.** Create a minimal `src-tauri/` project with a loading page, app icon, and macOS bundle configuration. On launch, start the packaged server bound to loopback, wait for its health endpoint, then navigate the window to it. Show a startup error if it fails, and terminate the child process when the app exits. No frontend IPC or plugins are needed for this design.

4. **Build and verify the installer.** Add a reproducible macOS packaging command, build the app and DMG, then test a fresh install: launch, font and RTL rendering, key entry, upload, playback, download, saved recordings, and relaunch persistence. Use mocked ElevenLabs calls for automated checks; run `uv run python -m unittest -v` to protect the existing UI and CLI.

5. **Document distribution.** Update installation instructions separately from the existing `uv` workflow. For distribution beyond local testing, sign and notarize the macOS build.

## Scope

macOS first. Windows and Linux need their own Python bundles and native installer builds; they should follow once the macOS packaging path is verified.
