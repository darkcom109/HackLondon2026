import os
import base64
from dotenv import load_dotenv
from anthropic import Anthropic

# Load .env
load_dotenv()

DEFAULT_MODEL = "claude-opus-4-6"
DEFAULT_MAX_TOKENS = 200


def _encode_image_base64(image_path: str) -> tuple[str, str]:
    """
    Returns (media_type, base64_data) for an image file.
    Supports .jpg/.jpeg/.png
    """

    ext = os.path.splitext(image_path)[1].lower()
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
    }
    media_type = media_types.get(ext)
    if media_type is None:
        raise ValueError(f"Unsupported image format: {ext}")

    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    return media_type, b64


def is_person_focused(image_path: str) -> tuple[int | None, str]:
    """
    Returns:
        (focus_score: 0-100 or None, reason: str)
    """

    api_key = os.getenv("CLAUDE_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("Missing API key.")

    model_name = os.getenv("CLAUDE_MODEL", DEFAULT_MODEL)
    try:
        max_tokens = int(os.getenv("CLAUDE_MAX_TOKENS", str(DEFAULT_MAX_TOKENS)))
    except ValueError:
        max_tokens = DEFAULT_MAX_TOKENS

    client = Anthropic(api_key=api_key)
    media_type, image_b64 = _encode_image_base64(image_path)

    prompt = (
        "You are analyzing a webcam image of someone studying.\n"
        "you ideally want them to sort of look at the webcam or looking down focused or writing\n"
        "you should be able to figure out if the person is not focused on their facial expression\n"
        "However you really need to analyse their face properly to ensure they are studying"
        "Task: Estimate how focused the person appears.\n\n"
        "Return EXACTLY this format:\n"
        "Focus Score: <integer from 0 to 100>\n"
        "Reason: <one short sentence>\n\n"
        "Guidelines:\n"
        "100 = fully focused, strong posture, looking at study material.\n"
        "70-90 = mostly focused with minor distraction.\n"
        "40-60 = partially distracted.\n"
        "10-30 = clearly distracted.\n"
        "0 = completely off-task.\n"
        "If you cannot see the person say focus mode is 0\n"
        "Reason: <one short sentence>\n"
    )

    message = client.messages.create(
        model=model_name,
        max_tokens=max_tokens,
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

    focus_score = None
    reason = ""
    for line in claude_output.splitlines():
        if line.lower().startswith("focus score:"):
            try:
                value = int(line.split(":", 1)[1].strip())
                if 0 <= value <= 100:
                    focus_score = value
                elif value == -1:
                    focus_score = None
            except ValueError:
                focus_score = None

        if line.lower().startswith("reason:"):
            reason = line.split(":", 1)[1].strip()

    if not reason:
        reason = "No focus reason returned."

    return focus_score, reason
