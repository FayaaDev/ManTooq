"""Entrypoint for the packaged local Streamlit server."""

import os
import sys
from pathlib import Path

from streamlit.web import cli


if __name__ == "__main__":
    bundle = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    os.chdir(bundle)
    sys.argv = ["streamlit", "run", str(bundle / "app" / "app.py"),
                "--global.developmentMode=false", "--server.address=127.0.0.1", "--server.headless=true",
                "--browser.gatherUsageStats=false", "--server.fileWatcherType=none",
                *sys.argv[1:]]
    cli.main()
