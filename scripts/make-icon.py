"""Draw the bundled app icon without storing generated binary files in git."""

import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw


icons = Path(__file__).resolve().parent.parent / "src-tauri" / "icons"
icons.mkdir(parents=True, exist_ok=True)
image = Image.new("RGBA", (1024, 1024), "#2254b4")
draw = ImageDraw.Draw(image)
draw.rounded_rectangle((405, 220, 619, 615), radius=105, fill="white")
draw.arc((320, 345, 704, 765), 0, 180, fill="white", width=50)
draw.line((512, 760, 512, 850), fill="white", width=50)
draw.line((410, 850, 614, 850), fill="white", width=45)
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
