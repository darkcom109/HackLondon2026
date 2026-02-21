# Imports OpenCV - accesses webcam, captures frames and saves
import cv2
import time
import os
import shutil
import json
from pathlib import Path
from datetime import datetime

from scanner import is_person_focused

FOCUS_HIGH_THRESHOLD = 70
FOCUS_LOW_THRESHOLD = 40
FOCUS_STATE_FILE = Path(__file__).resolve().parents[1] / "focus_state.json"

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

def scanner():
    output_folder = os.path.join("SCANNING", "captures")
    os.makedirs(output_folder, exist_ok=True)

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print("Cannot access camera")
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
