# The Three Stooges Project

Focus scanner + Tamagotchi simulation + optional ESP32 status bridge.

## What This Project Does
- Captures a webcam image every 10 seconds.
- Sends the image to Claude for a focus score (0-100) and a short reason.
- Writes the latest focus result to `focus_state.json`.
- Runs a Tamagotchi-style pet that reads `focus_state.json` and updates mood/health.
- Optionally sends updates to an ESP32 endpoint.

## Current Flow
1. `scanner/main.py` starts `Python game/Tomagatchi.py`.
2. `scanner/picture.py` captures webcam frames and calls Claude via `scanner/scanner.py`.
3. `scanner/picture.py` writes `focus_state.json`.
4. `Python game/Tomagatchi.py` reads `focus_state.json`, updates pet state, redraws, and can push mood/status to ESP32.

## Project Structure
- `scanner/main.py`: Entrypoint that launches scanner + Tamagotchi process.
- `scanner/picture.py`: Webcam capture loop, focus state writer, optional ESP32 focus sender.
- `scanner/scanner.py`: Claude API call + parser for `Focus Score` and `Reason`.
- `scanner/speaker.py`: Optional ElevenLabs TTS alert helper.
- `Python game/Tomagatchi.py`: Pet simulation, OLED/pygame rendering, ESP32 status sender, C++ array exporter.
- `Python game/tomagatchi_arrays.h`: Auto-generated C++ arrays for Arduino/ESP32 (generated file).

## Requirements
- Python 3.10+
- Webcam
- Dependencies:
  - `anthropic`
  - `python-dotenv`
  - `opencv-python`
  - `requests`
  - `pygame`
  - `elevenlabs` (optional, only if using speaker alerts)

Example install:

```bash
pip install anthropic python-dotenv opencv-python requests pygame elevenlabs
```

## Environment Variables (`.env`)
Set the values you need:

```env
# Required for Claude scanning
CLAUDE_API_KEY=your_anthropic_key

# Optional Claude tuning
CLAUDE_MODEL=claude-opus-4-6
CLAUDE_MAX_TOKENS=200

# Optional camera selection
CAMERA_INDEX=0

# Optional: scanner -> ESP32 (POST JSON)
ESP32_URL=http://<esp32-ip>/focus

# Optional: Tamagotchi -> ESP32 (GET query params)
ESP32_STATUS_URL=http://<esp32-ip>/status
```

## Run
Start everything (recommended):

```bash
python scanner/main.py
```

This launches:
- Tamagotchi window/process
- scanner loop that updates focus every 10 seconds

Run only Tamagotchi:

```bash
python "Python game/Tomagatchi.py"
```

Stop with `CTRL+C` in the scanner terminal.

## Data Contracts
### `focus_state.json`
Written by `scanner/picture.py` and consumed by `Python game/Tomagatchi.py`.

Example:

```json
{
  "timestamp": "2026-02-21T22:53:50",
  "focus_score": 55,
  "level": "medium",
  "reason": "Person appears partially focused."
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

Query params currently sent by `Python game/Tomagatchi.py`:
- `hunger`
- `happiness`
- `energy`
- `age`
- `current_frame`
- `mood`

The Tamagotchi also prints params each send in terminal logs.

## Export C++ Arrays For Arduino
`Python game/Tomagatchi.py` can export sprite/mood arrays as a C++ header:

```bash
python "Python game/Tomagatchi.py" --export-cpp
```

Optional output path:

```bash
python "Python game/Tomagatchi.py" --export-cpp "Python game/tomagatchi_arrays.h"
```

Generated header includes:
- `TOMA_FACE_*` packed face arrays
- `TOMA_RAW_*` raw 2D arrays
- mood/action/pattern constants

## Troubleshooting
- `Cannot access camera`:
  - Set `CAMERA_INDEX` in `.env` (try `0`, `1`, etc).
- `Claude scan failed` with `401 quota_exceeded`:
  - Check the billing/quota for the API key and the correct provider account.
- `model ... not_found_error`:
  - Set a valid `CLAUDE_MODEL` in `.env`.
- No sound output:
  - `scanner/speaker.py` needs an audio player (`ffplay`, `mpg123`, or `paplay`) and ElevenLabs key.

## Security Note
- Do not commit live API keys.
- `.env` is already ignored in `.gitignore`.
- If keys were ever exposed, rotate them.
