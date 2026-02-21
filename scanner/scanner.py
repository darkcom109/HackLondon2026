import os
import base64
from dotenv import load_dotenv
from anthropic import Anthropic

# Load .env
load_dotenv()

def _encode_image_base64(image_path: str) -> tuple[str, str]:
    """
    Returns (media_type, base64_data) for an image file.
    Supports .jpg/.jpeg
    """

    ext = os.path.splitext(image_path)[1].lower() # Obtains file format of image

    if ext in [".jpg", ".jpeg"]:
        media_type = "image/jpeg"

    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    return media_type, b64


def is_person_focused(image_path: str) -> str:
    """
    Sends an image to Claude and asks whether the person appears focused.
    Returns a short text answer.
    """
    api_key = os.getenv("CLAUDE_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("Missing API key. Set CLAUDE_API_KEY (or ANTHROPIC_API_KEY) in your .env")

    client = Anthropic(api_key=api_key)

    media_type, image_b64 = _encode_image_base64(image_path)

    prompt = (
        "You are analyzing a webcam image of someone studying.\n"
        "Task: Decide if the person appears to be FOCUSED: True or False\n"
        "Use visible cues only (posture, gaze direction, phone use, off-task behavior).\n"
        "Return exactly this format:\n"
        "FOCUSED: True or False\n"
        "Reason: <one short sentence>\n"
        "If you cannot tell, return NOT SURE with the same format."
    )

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=200,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_b64,
                        },
                    },
                ],
            }
        ],
    )

    # Claude returns a list of content blocks; we join all text blocks.
    return "".join(block.text for block in message.content if getattr(block, "type", None) == "text")