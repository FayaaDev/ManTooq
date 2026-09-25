"""Generate bundled app icons from the shared logo."""

import subprocess
import sys
from pathlib import Path

from PIL import Image


icons = Path(__file__).resolve().parent.parent / "src-tauri" / "icons"
icons.mkdir(parents=True, exist_ok=True)
image = Image.open(Path(__file__).resolve().parent.parent / "app" / "font" / "logobg.png").convert("RGBA")
image = image.resize((1024, 1024), Image.Resampling.LANCZOS)
image.save(icons / "icon.png")
image.save(icons / "icon.ico", sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])
iconset = icons / "icon.iconset"
iconset.mkdir(exist_ok=True)
for size in (16, 32, 128, 256, 512):
    for scale in (1, 2):
        image.resize((size * scale, size * scale), Image.Resampling.LANCZOS).save(
            iconset / f"icon_{size}x{size}{'@2x' if scale == 2 else ''}.png"
        )
if sys.platform == "darwin":
    subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(icons / "icon.icns")], check=True)
