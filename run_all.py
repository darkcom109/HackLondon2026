import os
import subprocess
import sys
from pathlib import Path

try:
    import requests
except Exception:
    requests = None

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None


def _check_esp_reachable() -> None:
    esp_base = os.getenv("ESP32_STATUS_URL", os.getenv("ESP32_URL", "")).strip()
    if not esp_base:
        print("ESP32_URL not set; skipping ESP ping check.")
        return

    ping_url = esp_base.rstrip("/")
    if ping_url.endswith("/set"):
        ping_url = ping_url[:-4] + "/ping"
    elif not ping_url.endswith("/ping"):
        ping_url = ping_url + "/ping"

    if requests is None:
        print("requests not installed; skipping ESP ping check.")
        return

    try:
        response = requests.get(ping_url, timeout=2)
        print(f"ESP ping {ping_url}: {response.status_code} {response.text}")
    except requests.RequestException as exc:
        print(f"ESP ping failed ({ping_url}): {exc}")


def main() -> int:
    project_root = Path(__file__).resolve().parent
    scanner_main = project_root / "scanner" / "main.py"

    if load_dotenv is not None:
        load_dotenv(project_root / ".env")

    if not scanner_main.exists():
        print(f"Cannot find launcher: {scanner_main}")
        return 1

    _check_esp_reachable()

    cmd = [sys.executable, str(scanner_main)]
    return subprocess.call(cmd, cwd=str(project_root))


if __name__ == "__main__":
    raise SystemExit(main())
