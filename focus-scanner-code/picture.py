# Imports OpenCV - accesses webcam, captures frames and saves
import cv2
import time
import os
import shutil
import json
import requests
from pathlib import Path
from datetime import datetime
import threading
import platform

from scanner import is_person_focused

try:
    from speaker import text_to_speech
except Exception:
    text_to_speech = None

FOCUS_HIGH_THRESHOLD = 70
FOCUS_LOW_THRESHOLD = 40
FOCUS_STATE_FILE = Path(__file__).resolve().parents[1] / "focus_state.json"
ESP32_URL = os.getenv("ESP32_URL", "").strip()
ESP32_TIMEOUT_SECONDS = 3
SPEAKER_ALERT_THRESHOLD = 40
SPEAKER_ALERT_COOLDOWN_SECONDS = 60
_last_speaker_alert_at = 0.0

def _focus_level(focus_score):
    if focus_score is None:
        return "unknown"
    if focus_score >= FOCUS_HIGH_THRESHOLD:
        return "high"
    if focus_score <= FOCUS_LOW_THRESHOLD:
        return "low"
    return "medium"

def write_focus_state(focus_score, reason):
    payload = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "focus_score": focus_score,
        "level": _focus_level(focus_score),
        "reason": reason or "",
    }
    FOCUS_STATE_FILE.write_text(json.dumps(payload), encoding="utf-8")
    return payload["level"]

def send_focus_to_esp32(focus_score, focus_level, reason):
    if not ESP32_URL:
        return False

    payload = {
        "focus_score": focus_score,
        "focus_level": focus_level,
        "reason": reason or "",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }

    try:
        response = requests.post(ESP32_URL, json=payload, timeout=ESP32_TIMEOUT_SECONDS)
        response.raise_for_status()
        return True
    except requests.RequestException as exc:
        print(f"ESP32 request failed: {exc}")
        return False

def _speak_async(message):
    if text_to_speech is None:
        return
    thread = threading.Thread(target=text_to_speech, args=(message,), daemon=True)
    thread.start()

def maybe_speak_focus_alert(focus_score, reason):
    global _last_speaker_alert_at

    if text_to_speech is None:
        return
    if focus_score is None:
        return
    if focus_score > SPEAKER_ALERT_THRESHOLD:
        return

    now = time.time()
    if now - _last_speaker_alert_at < SPEAKER_ALERT_COOLDOWN_SECONDS:
        return

    _last_speaker_alert_at = now
    msg = "Quick focus check. You seem distracted."
    if reason:
        msg = f"Quick focus check. {reason}"
    _speak_async(msg)

def scanner():
    output_folder = os.path.join("SCANNING", "captures")
    os.makedirs(output_folder, exist_ok=True)

    camera_index = int(os.getenv("CAMERA_INDEX", "0"))

    if platform.system().lower().startswith("win"):
        cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    else:
        cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        print(f"Cannot access camera (index={camera_index}).")
        print("Try setting CAMERA_INDEX=1 (or another index) in .env.")
        exit()

    print("Capturing an image every 10 seconds...")
    print("Press CTRL+C to stop")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame")
                break

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(output_folder, f"capture_{timestamp}.jpg")

            cv2.imwrite(filename, frame)
            print(f"\nSaved {filename}")

            # Ask Claude if the person is focused
            try:
                focused, reason = is_person_focused(filename)

                focus_level = write_focus_state(focused, reason)
                send_focus_to_esp32(focused, focus_level, reason)
                maybe_speak_focus_alert(focused, reason)

                print("Focused:", focused)
                print("Focus level:", focus_level)

                # CALL TOMAGATCHI FUNCTION
                print("Claude says:")
                print("Reason:", reason)

            except Exception as e:
                print(f"Claude scan failed: {e}")

            time.sleep(10)

    except KeyboardInterrupt:
        print("\nStopping capture...")

    finally:
        cap.release()
        cv2.destroyAllWindows()

        if os.path.exists(output_folder):
            shutil.rmtree(output_folder)
            print("Capture folder deleted")
