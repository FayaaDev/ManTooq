#!/bin/sh
set -eu

cd "$(dirname "$0")/.."

uv run --with pyinstaller==6.22.3 pyinstaller --noconfirm --clean --onedir \
  --codesign-identity "${APPLE_SIGNING_IDENTITY:--}" \
  --name mantooq-server \
  --collect-all streamlit --collect-all streamlit_shadcn_ui \
  --paths app --hidden-import arabic_tts \
  --add-data app/app.py:app --add-data app/font:app/font \
  --add-data .streamlit/config.toml:.streamlit \
  app/desktop_server.py

# Neither credentials nor local recordings belong in the installer.
uv run --with pillow==12.3.0 python scripts/make-icon.py
npx --yes @tauri-apps/cli@2.11.5 build --bundles app,dmg
