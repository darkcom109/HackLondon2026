import json
import os
from pathlib import Path
import time
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

try:
    import requests
except Exception:
    requests = None

runOnDevice=False
width, height=128, 64
FOCUS_STATE_FILE = Path(__file__).resolve().parents[1] / "focus_state.json"
FOCUS_HIGH_THRESHOLD = 70
FOCUS_LOW_THRESHOLD = 40
lastFocusTimestamp = None
ESP32_FACE_URL = os.getenv("ESP32_FACE_URL", os.getenv("ESP32_URL", "")).strip()
ESP32_FACE_TIMEOUT_SECONDS = 2
ESP32_FACE_MIN_INTERVAL_MS = 100
lastFacePayloadKey = None
lastFacePushMs = 0
lastFacePushErrorMs = 0
ESP32_STATUS_URL = os.getenv("ESP32_STATUS_URL", ESP32_FACE_URL).strip()
CALM_PATTERN = (0, 1, 1, 0, 0, -1, -1, 0)
ENERGETIC_PATTERN = (0, 1, 2, 1, 0, -1, -2, -1)
SWAY_PATTERN = (0, 0, 1, 0, 0, 0, -1, 0)
ACTIONS = ("Focus",)

# Core gameplay tuning. The previous values drained stats too quickly.
UPDATE_INTERVAL_MS = 5000
FOCUS_HEALTH_GAIN = 8
FOCUS_HEALTH_LOSS = 8
FOCUS_HEALTH_MINOR_GAIN = 4
FOCUS_GOOD_THRESHOLD = 55
FOCUS_VERY_LOW_THRESHOLD = 20

FOCUS_REACTION_MS = 4000
ANIMATION_INTERVAL_MS = 120

focusReactionMood = None
focusReactionUntilMs = 0

pet={
    "health": 100,
    "age": 0,
    "current_frame": 0,
}

framesIndividual={
    "happy": [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0],
    [0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0],
    [0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,0,0,0,0,0],
    [0,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,0,0,0,0],
    [0,0,0,0,0,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,0,0,0,0],
    [0,0,0,0,0,0,1,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,1,0,0,0,0,0],
    [0,0,0,0,0,0,1,0,0,1,0,0,0,1,1,1,1,1,1,1,0,0,0,0,1,0,0,1,0,0,0,0,0],
    [0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0],
    [0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0],
    [0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0],
    [0,0,1,1,1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1,1,0],
    [0,0,1,1,1,1,1,1,1,1,0,0,0,1,1,1,1,1,1,1,1,0,0,0,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,0,0,0,1,1,1,1,1,1,1,1,0,0,0,1,1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,1,1,1,0,0,0,1,1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,1,1,1,1,1,0,0,0,1,1,1,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1],
    [0,0,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,0,1,1,1,1,0,1,1,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,0,0,1,1,1,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,1,1,1,0,0],
    [0,0,0,1,1,0,0,0,1,1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1,1,0,0,0,1,1,0,0],
    [0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1,1,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,0,0,1,1,1,1,1,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0],
    ],
    "crying": [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0],
    [0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0],
    [0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,0,0,0,0,0],
    [0,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,0,0,0,0],
    [0,0,0,0,0,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,0,0,0,0],
    [0,0,0,0,0,0,1,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,1,0,0,0,0,0],
    [0,0,0,0,0,0,1,0,0,1,0,0,0,1,1,1,1,1,1,1,0,0,0,0,1,0,0,1,0,0,0,0,0],
    [0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0],
    [0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0],
    [0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0],
    [0,0,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1,0],
    [0,0,1,1,1,1,1,1,1,1,0,0,0,1,1,1,1,1,1,1,1,0,0,0,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1,1],
    [1,0,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,0,0,0,0],
    [1,1,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1,1,0],
    [1,1,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1,1,1],
    [1,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1],
    [1,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,1,1,1,0,0,0,0,0,1,1,1,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1],
    [0,0,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,0,1,1,1,1,0,1,1,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,0,0,1,1,1,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,1,1,1,0,0],
    [0,0,0,1,1,0,0,0,1,1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1,1,0,0,0,1,1,0,0],
    [0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1,1,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,0,0,1,1,1,1,1,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0],
    ],
    "sad": [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0],
    [0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0],
    [0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,0,0,0,0,0],
    [0,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,0,0,0,0],
    [0,0,0,0,0,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,0,0,0,0],
    [0,0,0,0,0,0,1,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,1,0,0,0,0,0],
    [0,0,0,0,0,0,1,0,0,1,0,0,0,1,1,1,1,1,1,1,0,0,0,0,1,0,0,1,0,0,0,0,0],
    [0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0],
    [0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0],
    [0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0],
    [0,0,1,1,1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1,1,0],
    [0,0,1,1,1,1,1,1,1,1,0,0,0,1,1,1,1,1,1,1,1,0,0,0,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,0,0,0,1,1,1,1,1,1,1,1,0,0,0,1,1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,1,1,1,0,0,0,0,0,1,1,1,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1],
    [0,0,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,0,1,1,1,1,0,1,1,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,0,0,1,1,1,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,1,1,1,0,0],
    [0,0,0,1,1,0,0,0,1,1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1,1,0,0,0,1,1,0,0],
    [0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1,1,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,0,0,1,1,1,1,1,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0],
    ],
    "depressed": [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0],
    [0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0],
    [0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,0,0,0,0,0],
    [0,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,0,0,0,0],
    [0,0,0,0,0,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,0,0,0,0],
    [0,0,0,0,0,0,1,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,1,0,0,0,0,0],
    [0,0,0,0,0,0,1,0,0,1,0,0,0,1,1,1,1,1,1,1,0,0,0,0,1,0,0,1,0,0,0,0,0],
    [0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0],
    [0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0],
    [0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0],
    [0,0,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1,0],
    [0,0,1,1,1,1,1,1,1,1,0,0,0,1,1,1,1,1,1,1,1,0,0,0,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1,1],
    [1,0,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,0,0,0,0],
    [1,1,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1,1,0],
    [1,1,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1,1,1],
    [1,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1],
    [1,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,1,1,1,0,0,0,0,0,1,1,1,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1],
    [0,1,1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1,1],
    [0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,0,1,1,1,1,0,1,1,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,0,0,1,1,1,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,1,1,1,0,0],
    [0,0,0,1,1,0,0,0,1,1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1,1,0,0,0,1,1,0,0],
    [0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1,1,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,0,0,1,1,1,1,1,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,0,1,1,1,1,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0],
    ],
}

def packMono_HLSB(pixels2D):
    #Converts the valid pixels above into MONO_HLSB if needed.
    height=len(pixels2D)
    if height==0:
        raise ValueError("No rows in sprite.")
    width=len(pixels2D[0])
    for r in pixels2D:
        if len(r)!=width:
            raise ValueError("Sprite rows are not all the same width.")
    bytesPerRow=(width+7)//8
    out = bytearray(bytesPerRow*height)
    for y, row in enumerate(pixels2D):
        rowBase = y*bytesPerRow
        for x, v in enumerate(row):
            if v:
                out[rowBase+(x>>3)] |= (1<<(x&7))
    return (width, height, bytes(out))
def resizePackMono_HSLB(pixels2D, width=32, height=32):
    croppedRows=pixels2D[:height]
    while len(croppedRows)<height:
        croppedRows.append([0]*width)
    fixed=[]
    for row in croppedRows:
        newRow = row[:width]
        if len(newRow)<width:
            newRow = newRow+[0]*(width-len(newRow))
        fixed.append(newRow)
    bytesPerRow=(width+7)//8
    out = bytearray(bytesPerRow*height)

    for y, row in enumerate(fixed):
        rowBase = y*bytesPerRow
        for x, v in enumerate(row):
            if v:
                out[rowBase+(x>>3)] |= (1<<(x&7))
    return (width, height, bytes(out))

#x,y,b=packMono_HLSB(framesIndividual["happy"])
#print(x, y, list(b))

frames={
    "loving": (
    32, 32,
    bytes([
        0, 96, 3, 4, 64, 240, 7, 6, 192, 240, 7, 7, 95, 225, 3, 253,
        78, 193, 1, 117, 68, 226, 135, 36, 192, 255, 255, 7, 192, 255, 255, 7,
        248, 255, 255, 63, 248, 255, 255, 63, 252, 247, 255, 127, 252, 227, 143, 127,
        254, 243, 159, 255, 254, 255, 255, 255, 254, 255, 255, 255, 254, 255, 255, 255,
        253, 255, 255, 15, 255, 255, 255, 127, 255, 255, 255, 255, 255, 255, 255, 255,
        254, 255, 255, 255, 254, 249, 63, 255, 254, 251, 159, 255, 254, 227, 207, 255,
        252, 31, 248, 127, 188, 249, 255, 127, 56, 252, 127, 56, 24, 255, 252, 49,
        240, 255, 249, 31, 128, 255, 243, 3, 0, 252, 247, 0, 0, 224, 31, 0,
    ])
    ),
    "happy": resizePackMono_HSLB(framesIndividual["happy"], width=32, height=32),
    "happy": (
    32, 32,
    bytes([
        0, 0, 0, 4, 64, 0, 0, 6, 192, 0, 0, 7, 64, 1, 0, 5,
        64, 1, 0, 5, 64, 226, 135, 4, 192, 255, 255, 7, 192, 255, 255, 7,
        248, 255, 255, 63, 248, 255, 255, 63, 252, 247, 255, 127, 252, 227, 143, 127,
        254, 243, 159, 255, 254, 255, 255, 255, 254, 255, 255, 255, 254, 255, 255, 255,
        253, 255, 255, 15, 255, 255, 255, 127, 255, 255, 255, 255, 255, 255, 255, 255,
        254, 255, 255, 255, 254, 249, 63, 255, 254, 251, 159, 255, 254, 227, 207, 255,
        252, 31, 248, 127, 188, 249, 255, 127, 56, 252, 127, 56, 24, 255, 252, 49,
        240, 255, 249, 31, 128, 255, 243, 3, 0, 252, 247, 0, 0, 224, 31, 0,
    ])
    ),
    "sad": (
    32, 32,
    bytes([
        0, 0, 0, 4, 64, 0, 0, 6, 192, 0, 0, 7, 64, 1, 0, 5,
        64, 1, 0, 5, 64, 226, 135, 4, 192, 255, 255, 7, 192, 255, 255, 7,
        248, 255, 255, 63, 248, 255, 255, 63, 252, 247, 255, 127, 252, 227, 143, 127,
        254, 243, 159, 255, 254, 255, 255, 255, 254, 255, 255, 255, 254, 255, 255, 255,
        253, 255, 255, 15, 255, 255, 255, 127, 255, 255, 255, 255, 255, 255, 255, 255,
        254, 255, 255, 255, 254, 255, 255, 255, 254, 255, 255, 255, 254, 249, 63, 255,
        252, 31, 224, 127, 188, 249, 255, 127, 56, 252, 127, 56, 24, 255, 252, 49,
        240, 255, 249, 31, 128, 255, 243, 3, 0, 252, 247, 0, 0, 224, 31, 0,
    ])
    ),
    "crying": (
    32, 32,
    bytes([
        0, 0, 0, 4, 64, 0, 0, 6, 192, 0, 0, 7, 64, 1, 0, 5,
        64, 1, 0, 5, 64, 226, 135, 4, 192, 255, 255, 7, 192, 255, 255, 7,
        248, 255, 255, 63, 248, 255, 255, 63, 252, 247, 223, 127, 252, 227, 143, 127,
        254, 247, 223, 255, 254, 255, 255, 255, 254, 255, 255, 255, 254, 251, 223, 255,
        253, 255, 223, 15, 255, 239, 239, 127, 255, 255, 255, 255, 255, 247, 191, 255,
        254, 255, 191, 255, 254, 255, 255, 255, 254, 255, 255, 255, 254, 249, 63, 255,
        252, 31, 224, 127, 188, 249, 255, 127, 56, 252, 127, 56, 24, 255, 252, 49,
        240, 255, 249, 31, 128, 255, 243, 3, 0, 252, 247, 0, 0, 224, 31, 0,
    ])
    ),
    "depressed": (
    32, 32,
    bytes([
        0, 0, 0, 4, 64, 0, 0, 6, 192, 0, 0, 7, 64, 1, 0, 5,
        64, 1, 0, 5, 64, 226, 135, 4, 192, 255, 255, 7, 192, 255, 255, 7,
        248, 255, 255, 63, 248, 255, 255, 63, 252, 247, 223, 127, 252, 227, 143, 127,
        254, 247, 223, 255, 254, 255, 255, 255, 254, 255, 255, 255, 254, 251, 223, 255,
        253, 255, 223, 15, 255, 239, 239, 127, 255, 255, 255, 255, 255, 247, 191, 255,
        254, 255, 191, 255, 254, 255, 255, 255, 254, 31, 224, 255, 254, 193, 3, 255,
        252, 255, 255, 127, 188, 241, 255, 127, 56, 252, 127, 56, 24, 255, 252, 49,
        240, 255, 249, 31, 128, 255, 243, 3, 0, 252, 247, 0, 0, 224, 31, 0,
    ])
    ),
    "neutral": (
    32, 32,
    bytes([
        0, 0, 0, 4, 64, 0, 0, 6, 192, 0, 0, 7, 64, 1, 0, 5,
        64, 1, 0, 5, 64, 226, 135, 4, 192, 255, 255, 7, 192, 255, 255, 7,
        248, 255, 255, 63, 248, 255, 255, 63, 252, 247, 255, 127, 252, 227, 143, 127,
        254, 243, 159, 255, 254, 255, 255, 255, 254, 255, 255, 255, 254, 255, 255, 255,
        253, 255, 255, 15, 255, 255, 255, 127, 255, 255, 255, 255, 255, 255, 255, 255,
        254, 255, 255, 255, 254, 3, 128, 255, 254, 255, 255, 255, 254, 255, 255, 255,
        252, 255, 255, 127, 188, 241, 255, 127, 56, 252, 127, 56, 24, 255, 252, 49,
        240, 255, 249, 31, 128, 255, 243, 3, 0, 252, 247, 0, 0, 224, 31, 0,
    ])
    ),
    "dead": (
    32, 32,
    bytes([
        0, 0, 0, 4, 64, 0, 0, 6, 192, 0, 0, 6, 64, 0, 0, 6,
        192, 0, 0, 6, 192, 98, 134, 7, 192, 127, 254, 7, 192, 127, 255, 7,
        248, 127, 254, 63, 120, 254, 255, 63, 60, 235, 239, 127, 188, 247, 223, 127,
        254, 235, 239, 255, 254, 255, 255, 251, 222, 255, 255, 251, 222, 251, 223, 249,
        221, 255, 223, 13, 159, 239, 239, 125, 191, 255, 255, 251, 191, 247, 191, 247,
        158, 255, 191, 231, 222, 255, 255, 239, 222, 31, 224, 255, 254, 193, 3, 255,
        252, 255, 255, 127, 188, 241, 255, 127, 56, 252, 127, 56, 24, 255, 252, 49,
        240, 255, 249, 31, 128, 255, 243, 3, 0, 252, 247, 0, 0, 224, 31, 0,
    ])
    ),
}

def _cpp_int_values(values, per_line=16):
    lines = []
    for i in range(0, len(values), per_line):
        chunk = ", ".join(str(int(v)) for v in values[i:i + per_line])
        lines.append(f"    {chunk}")
    return ",\n".join(lines)

def _cpp_2d_rows(rows):
    lines = []
    for row in rows:
        row_values = ", ".join(str(int(v)) for v in row)
        lines.append(f"    {{{row_values}}},")
    return "\n".join(lines)

def export_cpp_arrays(output_path=None):
    out_path = Path(output_path) if output_path else Path(__file__).with_name("tomagatchi_arrays.h")
    moods = list(frames.keys())
    header_lines = [
        "// Auto-generated from Tomagatchi.py",
        "#pragma once",
        "#include <stdint.h>",
        "",
        f"const int8_t TOMA_CALM_PATTERN[{len(CALM_PATTERN)}] = {{{', '.join(str(v) for v in CALM_PATTERN)}}};",
        f"const int8_t TOMA_ENERGETIC_PATTERN[{len(ENERGETIC_PATTERN)}] = {{{', '.join(str(v) for v in ENERGETIC_PATTERN)}}};",
        f"const int8_t TOMA_SWAY_PATTERN[{len(SWAY_PATTERN)}] = {{{', '.join(str(v) for v in SWAY_PATTERN)}}};",
        f"const char* const TOMA_ACTIONS[{len(ACTIONS)}] = {{{', '.join(f'\"{a}\"' for a in ACTIONS)}}};",
        f"const char* const TOMA_MOODS[{len(moods)}] = {{{', '.join(f'\"{m}\"' for m in moods)}}};",
        "",
    ]

    for mood, rows in framesIndividual.items():
        row_count = len(rows)
        col_count = len(rows[0]) if row_count else 0
        arr_name = f"TOMA_RAW_{mood.upper()}"
        header_lines.append(f"const uint8_t {arr_name}[{row_count}][{col_count}] = {{")
        header_lines.append(_cpp_2d_rows(rows))
        header_lines.append("};")
        header_lines.append("")

    for mood in moods:
        width_px, height_px, bitmap = frames[mood]
        arr_name = f"TOMA_FACE_{mood.upper()}"
        header_lines.append(f"const uint8_t {arr_name}[{len(bitmap)}] = {{")
        header_lines.append(_cpp_int_values(bitmap))
        header_lines.append("};")
        header_lines.append(f"const uint8_t {arr_name}_W = {int(width_px)};")
        header_lines.append(f"const uint8_t {arr_name}_H = {int(height_px)};")
        header_lines.append("")

    out_path.write_text("\n".join(header_lines), encoding="utf-8")
    print(f"C++ arrays exported to {out_path}")

if __name__ == "__main__" and "--export-cpp" in sys.argv:
    arg_index = sys.argv.index("--export-cpp")
    output_arg = sys.argv[arg_index + 1] if (arg_index + 1) < len(sys.argv) else None
    export_cpp_arrays(output_arg)
    raise SystemExit(0)

currentAction = 0
actions=ACTIONS
totalActions=len(actions)

def clamp(value, minVal=0, maxVal=100):
    return max(minVal, min(maxVal, value))

def incrementAttribute(name, change):
    pet[name]=clamp(pet[name]+change)

def now_ms():
    return int(time.monotonic() * 1000)

def set_focus_reaction(mood):
    global focusReactionMood, focusReactionUntilMs
    focusReactionMood = mood
    focusReactionUntilMs = now_ms() + FOCUS_REACTION_MS

def updatePet():
    # Keep age tracking, but health is only changed by focus score.
    pet["age"] += 1

def perform_action(action):
    # Manual action is intentionally disabled for one-stat mode.
    return

def apply_focus_score(focus_score):
    if focus_score is None:
        set_focus_reaction("neutral")
        return "unknown"

    score = clamp(focus_score, 0, 100)

    if score >= FOCUS_HIGH_THRESHOLD:
        incrementAttribute("health", FOCUS_HEALTH_GAIN)
        set_focus_reaction("loving")
        return "high"

    if score >= FOCUS_GOOD_THRESHOLD:
        incrementAttribute("health", FOCUS_HEALTH_MINOR_GAIN)
        set_focus_reaction("happy")
        return "good"

    if score <= FOCUS_VERY_LOW_THRESHOLD:
        incrementAttribute("health", -FOCUS_HEALTH_LOSS)
        set_focus_reaction("crying")
        return "very_low"

    if score <= FOCUS_LOW_THRESHOLD:
        incrementAttribute("health", -FOCUS_HEALTH_LOSS)
        set_focus_reaction("sad")
        return "low"

    set_focus_reaction("neutral")
    return "medium"

def apply_latest_focus_signal():
    global lastFocusTimestamp

    if not FOCUS_STATE_FILE.exists():
        return False

    try:
        payload = json.loads(FOCUS_STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False

    timestamp = payload.get("timestamp")
    if not timestamp or timestamp == lastFocusTimestamp:
        return False

    lastFocusTimestamp = timestamp

    raw_score = payload.get("focus_score")
    try:
        focus_score = int(raw_score) if raw_score is not None else None
    except (TypeError, ValueError):
        focus_score = None

    level = apply_focus_score(focus_score)
    reason = payload.get("reason", "")
    print(f"Focus update [{level}] score={focus_score} reason={reason}")
    return True

def moodName():
    health = pet["health"]
    if health <= 0:
        return "dead"
    if health <= 20:
        return "depressed"
    if focusReactionMood and now_ms() < focusReactionUntilMs:
        return focusReactionMood
    if health <= 35:
        return "crying"
    if health <= 50:
        return "sad"
    if health <= 65:
        return "neutral"
    if health <= 80:
        return "happy"
    return "loving"

def send_status_to_esp32(mood):
    global lastFacePayloadKey, lastFacePushMs, lastFacePushErrorMs

    if not ESP32_STATUS_URL or requests is None:
        return False

    now = now_ms()
    payload_key = (mood, int(pet["health"]), int(pet["current_frame"] % 8))

    # Skip duplicates if they are generated too quickly.
    if payload_key == lastFacePayloadKey and (now - lastFacePushMs) < ESP32_FACE_MIN_INTERVAL_MS:
        return False

<<<<<<< HEAD:Python-game/Tomagatchi.py
    health_value = int(pet["health"])
    params = {
        "hunger": health_value,
        "happiness": health_value,
        "energy": health_value,
        "age": int(pet["age"]),
        "current_frame": int(pet["current_frame"] % 8),
        "mood": mood,
    }
    print(f"ESP32 status params: {json.dumps(params)}")

    try:
        response = requests.get(ESP32_STATUS_URL, params=params, timeout=ESP32_FACE_TIMEOUT_SECONDS)
=======
    payload = {
        "type": "tomagatchi_status",
        "status": mood,
        "health": int(pet["health"]),
        "frame": int(pet["current_frame"] % 8),
        "timestamp_ms": now,
    }
    print(f"ESP32 status payload: {json.dumps(payload)}")

    try:
        response = requests.post(
            ESP32_STATUS_URL,
            json=payload,
            timeout=ESP32_FACE_TIMEOUT_SECONDS,
        )
>>>>>>> 82a6f80 (fix: fix this now):Python game/Tomagatchi.py
        response.raise_for_status()
        lastFacePayloadKey = payload_key
        lastFacePushMs = now
        return True
    except requests.RequestException as exc:
        # Keep logs readable while still surfacing failures.
        if now - lastFacePushErrorMs > 2000:
            print(f"ESP32 status push failed: {exc}")
            lastFacePushErrorMs = now
        return False

def drawPet(oled):
    oled.fill(0)

    #oled.circle(64, 32, 10, 1) #HEad
    #oled.fill_rect(58, 28, 4, 4, 1)#Left eye
    #oled.fill_rect(66, 28, 4, 4, 1)#Right eye
    #oled.hline(58, 38, 10, 1)#Mouth

    #oled.fill_rect(54, 22, 20, 20, 0)
    #oled.fill_rect(54, 22, 20, 20, 1)
    #oled.fill_rect(58, 28, 3, 3, 0)#Left eye hole.
    #oled.fill_rect(67, 28, 3, 3, 0)#Right eye hole.
    #oled.hline(58, 38, 12, 0) #Mouth hole.

    mood=moodName()
    sprite=frames[mood]
    pattern = ENERGETIC_PATTERN if mood in ("loving", "happy") else CALM_PATTERN
    phase = pet["current_frame"] % len(pattern)
    bob = pattern[phase]
    sway = 0 if mood in ("depressed", "dead") else SWAY_PATTERN[phase]

    sprite_x=(width-sprite[0])//2 + sway
    sprite_y=5 + bob
    blit_sprite(oled, sprite, sprite_x, sprite_y)

    textOutput="Health:"+str(pet["health"])
    oled.text(textOutput[:21], 0, 50, 1)

    #currentAction
    textInterval=width//totalActions
    y=42
    for i, action in enumerate(actions):
        x=i*textInterval
        if i==currentAction:
            oled.text("="+action, x, 42, 1)
        else:
            oled.text(" "+action, x, 42, 1)
    oled.show()
    send_status_to_esp32(mood)

if runOnDevice:
    from machine import Pin, I2C
    import ssd1306
    import framebuf

    i2c = I2C(0, scl=Pin(32), sda=Pin(21))
    oled=ssd1306.SSD1306_I2C(128, 64, i2c)

    buttonNext = Pin(12, Pin.IN, Pin.PULL_UP)
    buttonSelect=Pin(13, Pin.IN, Pin.PULL_UP)

    def tick_ms():
        return time.ticks_ms()
    def ticks_diff(a, b):
        return time.ticks_diff(a, b)
    def sleep_ms(ms):
        time.sleep_ms(ms)
    def next_pressed():
        return not buttonNext.value()
    def select_pressed():
        return not buttonSelect.value()

    def blit_sprite(oled, sprite, x, y):
        width, height, data = sprite
        buffer = bytearray(data)
        frameBuffer = framebuf.FrameBuffer(buffer, width, height, framebuf.MONO_HLSB)
        oled.blit(frameBuffer, x, y)
else:
    import pygame
    import sys

    #ESP model is ESP32 C3SuperMini

    class FakeOled:
        def __init__(self, scale=6):
            self.width, self.height = width, height
            self.scale=scale
            self.frame=[[0]*self.width for _ in range(self.height)]

            pygame.init()
            self.screen=pygame.display.set_mode((self.width*self.scale, self.height*self.scale))
            pygame.display.set_caption("Tomagatchi-9000")
            self.clock = pygame.time.Clock()
            self.font = None
            try:
                pygame.font.init()
                self.font = pygame.font.Font(None, 10)
            except Exception as exc:
                print(f"Warning: pygame font unavailable, text overlay disabled ({exc})")
        def fill(self, colour):
            v=1 if colour else 0
            for y in range(self.height):
                for x in range(self.width):
                    self.frame[y][x] = v
        def pixel(self, x, y, colour=1):
            if 0<=x<self.width and 0<=y<self.height:
                self.frame[y][x]=colour
        def hline(self, x, y, length, colour=1):
            for i in range(length):
                if x+i>=self.width:
                    break
                self.pixel(x+i,y,colour)
        def fill_rect(self, x, y, width, height, colour=1):
            for y2 in range(y, y+height):
                if y2>=self.height:
                    break
                for x2 in range(x, x+width):
                    if x2>=self.width:
                        break
                    self.pixel(x2, y2, colour)
        def text(self, message, x, y, colour=1):
            if self.font is None:
                return
            fg=(255, 255, 255) if colour==1 else (0,0,0)
            bg=(0, 0, 0)
            surface=  self.font.render(message, False, fg, bg)
            surfaceWidth, surfaceHeight = surface.get_size()
            for y2 in range(surfaceHeight):
                for x2 in range(surfaceWidth):
                    if 0<=x+x2<self.width and 0<=y+y2<self.height:
                        r, g, b, *rest = surface.get_at((x2, y2))
                        if r>128:
                            self.frame[y+y2][x+x2]=colour
        def _poll_events(self):
            self._next=False
            self._select=False
            for event in pygame.event.get():
                if event.type==pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type==pygame.KEYDOWN:
                    if event.key==pygame.K_n:
                        self._next=True
                    if event.key==pygame.K_s:
                        self._select=True
        def show(self):
            self._poll_events()
            self.screen.fill((0,0,0))
            for y in range(self.height):
                for x in range(self.width):
                    if self.frame[y][x]:
                        pygame.draw.rect(
                            self.screen,
                            (255,255,255),
                            (x*self.scale, y*self.scale, self.scale, self.scale)
                        )
            pygame.display.flip()
            self.clock.tick(60)
        def next_pressed(self):
            return self._next
        def select_pressed(self):
            return self._select
    oled=FakeOled(scale=6)
    def tick_ms():
        return int(time.monotonic()*1000)
    def ticks_diff(a, b):
        return a-b
    def sleep_ms(ms):
        time.sleep(ms/1000)
    def next_pressed():
        return oled.next_pressed()
    def select_pressed():
        return oled.select_pressed()
    def blit_sprite(oled, sprite, x, y):
        width, height, data = sprite
        bytesPerRow = (width+7) // 8
        for y2 in range(height):
            rowBase = y2 * bytesPerRow
            for x2 in range(width):
                b=data[rowBase+(x2//8)]
                bit=(b>>(x2%8)) & 1 #MONO_HLSB
                if bit:
                    oled.pixel(x+x2, y+y2, 1)

lastUpdate = tick_ms()
updateInterval = UPDATE_INTERVAL_MS
lastAnimation = tick_ms()
animationInterval = ANIMATION_INTERVAL_MS

drawPet(oled)

mainLoop=True
while mainLoop:
    #Every "updateInterval" seconds, the pet is updated and drawn. :)
    #if time.ticks_diff(time.ticks_ms(), lastUpdate) > updateInterval:
    #    lastUpdate=time.ticks_ms()
    #    updatePet()
    #    drawPet(oled)
    ##Buttons.
    #if not buttonNext.value():
    #    currentAction=(currentAction+1)%totalActions
    #    time.sleep_ms(200)
    #if not buttonSelect.value():
    #    perform_action(currentAction)
    #    drawPet()
    #    time.sleep_ms(200)
    now=tick_ms()
    needsRedraw = False

    if apply_latest_focus_signal():
        needsRedraw = True

    if ticks_diff(now, lastUpdate) > updateInterval:
        lastUpdate=now
        updatePet()
        needsRedraw = True
    if ticks_diff(now, lastAnimation) > animationInterval:
        lastAnimation = now
        pet["current_frame"] = (pet["current_frame"] + 1) % 1000000
        needsRedraw = True
    if next_pressed():
        currentAction=(currentAction+1)%totalActions
        needsRedraw = True
        sleep_ms(200)
    if select_pressed():
        perform_action(currentAction)
        needsRedraw = True
        sleep_ms(200)
    if needsRedraw:
        drawPet(oled)
    #Small idle to avoid overusing CPU. :)
    sleep_ms(10)
