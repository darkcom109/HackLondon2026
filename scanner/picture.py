# Imports OpenCV - accesses webcam, captures frames and saves
import cv2
import time
import os
import shutil
from datetime import datetime

from scanner import is_person_focused

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

                print("Focused:", focused)

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