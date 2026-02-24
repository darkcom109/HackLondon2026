# The Three Stooges Project

Webcam focus scanner + Tamagotchi game + ESP32 OLED bridge.

## Overview
This project captures webcam frames, asks Claude to estimate focus, and uses that score to drive a Tamagotchi pet state. The pet can also send status updates to an ESP32 so your OLED can show stats/mood.

## Current Repository Layout
- `focus-scanner-code/main.py`
- `focus-scanner-code/picture.py`
- `focus-scanner-code/scanner.py`
- `focus-scanner-code/speaker.py`
- `python-game-code/Tomagatchi.py`
- `python-game-code/tomagatchi_arrays.h`
- `arduino-code/sketch_feb21b/sketch_feb21b.ino`
- `focus_state.json`
- `run_all.py`

## Flow
1. `focus-scanner-code/picture.py` captures webcam images.
2. `focus-scanner-code/scanner.py` sends each image to Claude and gets:
   - `focus_score` (0-100)
   - `reason`
3. Scanner writes the result to root `focus_state.json`.
4. `python-game-code/Tomagatchi.py` reads `focus_state.json`, updates health/mood, and redraws.
5. Tamagotchi optionally sends status to ESP32 over HTTP.

## Requirements
- Python 3.10+
- Webcam
- Optional ESP32 board + SSD1306 OLED

Python packages:
- `anthropic`
- `python-dotenv`
- `opencv-python`
- `requests`
- `pygame`
- `elevenlabs` (optional, for speech alerts)

Install:

```bash
py -3 -m pip install anthropic python-dotenv opencv-python requests pygame elevenlabs
```

## Environment Variables (`.env`)

```env
# Claude
CLAUDE_API_KEY=your_anthropic_key
# or ANTHROPIC_API_KEY=...
CLAUDE_MODEL=claude-opus-4-6
CLAUDE_MAX_TOKENS=200

# Camera
CAMERA_INDEX=0

# Scanner -> ESP32 (POST JSON)
ESP32_URL=http://<esp32-ip>/focus

# Tamagotchi -> ESP32 (GET query params)
ESP32_STATUS_URL=http://<esp32-ip>/set

# Optional speech alerts
ELEVENLABS_API_KEY=your_elevenlabs_key
```

## Run
Recommended right now (2 terminals):

Terminal 1 (Tamagotchi):

```bash
py -3 python-game-code/Tomagatchi.py
```

Terminal 2 (scanner):

```bash
py -3 focus-scanner-code/picture.py
```

Stop with `Ctrl+C`.

## Data Contracts
### `focus_state.json` (root)
Produced by scanner and consumed by Tamagotchi.

Example:

```json
{
  "timestamp": "2026-02-24T02:42:00",
  "focus_score": 55,
  "level": "medium",
  "reason": "Person appears somewhat focused."
}
```

### Scanner -> ESP32 (`ESP32_URL`)
Method: `POST`

JSON body:
- `focus_score`
- `focus_level`
- `reason`
- `timestamp`

### Tamagotchi -> ESP32 (`ESP32_STATUS_URL`)
Method: `GET`

Query params:
- `hunger`
- `happiness`
- `energy`
- `age`
- `current_frame`
- `mood`

## Arduino Side
Current sketch path:
- `arduino-code/sketch_feb21b/sketch_feb21b.ino`

The sketch currently exposes:
- `GET /ping`
- `GET /set` (reads stats query params)

## Export C++ Arrays
Generate/update C++ arrays from the Python sprites:

```bash
py -3 python-game-code/Tomagatchi.py --export-cpp
```

Output:
- `python-game-code/tomagatchi_arrays.h`

## Notes
- `focus_state.json` must stay at repo root for scanner/game sync.
- Keep `.env` out of git (already ignored).
- If API keys were exposed, rotate them.
