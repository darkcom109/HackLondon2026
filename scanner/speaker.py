from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from playsound import playsound
import os

load_dotenv()

api_key = os.getenv("ELEVENLABS_API_KEY")
elevenlabs = ElevenLabs(api_key=api_key)

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
    playsound(filename)

    os.remove(filename)