from pathlib import Path

from dotenv import load_dotenv
from fishaudio import FishAudio
from fishaudio.utils import save

load_dotenv(Path(__file__).with_name(".env.local"))

client = FishAudio()  # reads FISH_API_KEY

audio = client.tts.convert(
    text=Path(__file__).with_name("text.txt").read_text().strip(),
    reference_id="5b67899dc9a34685ae09c94c890a606f",
    model="s2.1-pro-free",
)
save(audio, "output.mp3")
