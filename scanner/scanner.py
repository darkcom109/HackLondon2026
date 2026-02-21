import os
import base64
from dotenv import load_dotenv
from anthropic import Anthropic
from speaker import text_to_speech

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


def is_person_focused(image_path: str) -> tuple[bool | None, str]:
    """
    Returns:
        (focused: True/False/None, reason: str)
    """

    api_key = os.getenv("CLAUDE_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("Missing API key.")

    client = Anthropic(api_key=api_key)
    media_type, image_b64 = _encode_image_base64(image_path)

    prompt = (
        "You are analyzing a webcam image of someone studying.\n"
        "Task: Decide if the person appears to be FOCUSED.\n"
        "Return EXACTLY this format:\n"
        "Focused: True or False\n"
        "Reason: <one short sentence>\n"
        "If you cannot tell, return:\n"
        "Focused: NOT SURE\n"
        "Reason: <one short sentence>\n"
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

    claude_output = "".join(
        block.text for block in message.content
        if getattr(block, "type", None) == "text"
    ).strip()

    # ---------------------------
    # PARSE RESULT SAFELY
    # ---------------------------

    focused = None
    reason = ""

    lines = claude_output.splitlines()

    for line in lines:
        if line.lower().startswith("focused:"):
            value = line.split(":", 1)[1].strip().lower()
            if value == "true":
                focused = True
            elif value == "false":
                focused = False
            else:
                focused = None

        if line.lower().startswith("reason:"):
            reason = line.split(":", 1)[1].strip()

    # Optional: speak only the reason
    text_to_speech(reason)

    return focused, reason