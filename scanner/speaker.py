from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
import os
import subprocess

load_dotenv()

api_key = os.getenv("ELEVENLABS_API_KEY")
elevenlabs = ElevenLabs(api_key=api_key)


def _play_audio(filename):
    commands = [
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "error", filename],
        ["mpg123", "-q", filename],
        ["paplay", filename],
    ]

    for cmd in commands:
        try:
            completed = subprocess.run(cmd, check=False)
            if completed.returncode == 0:
                return True
        except FileNotFoundError:
            continue

    return False

def text_to_speech(text):
    audio = elevenlabs.text_to_speech.convert(
        text=f"{text}",
        voice_id="JBFqnCBsd6RMkjVDRZzb",
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )

    filename = "output.mp3"

    # Write generator chunks to file
    with open(filename, "wb") as f:
        for chunk in audio:
            f.write(chunk)

    # Play immediately
    played = _play_audio(filename)
    if not played:
        print("Warning: No audio player found (tried ffplay/mpg123/paplay).")

    os.remove(filename)
