import subprocess
import sys
from pathlib import Path

from picture import scanner as run_scanner

FOCUS_STATE_FILE = "focus_state.json"

def _start_tomagatchi(project_root: Path) -> subprocess.Popen:
    tomagatchi_path = project_root / "Python game" / "Tomagatchi.py"
    if not tomagatchi_path.exists():
        raise FileNotFoundError(f"Tomagatchi not found at {tomagatchi_path}")

    return subprocess.Popen(
        [sys.executable, str(tomagatchi_path)],
        cwd=str(project_root),
    )

def _delete_stale_focus_state(project_root: Path) -> None:
    focus_state_path = project_root / FOCUS_STATE_FILE
    if not focus_state_path.exists():
        return

    try:
        focus_state_path.unlink()
    except OSError as exc:
        print(f"Warning: failed to clear old focus state ({exc})")

if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    _delete_stale_focus_state(project_root)

    pet_process = _start_tomagatchi(project_root)
    print("Tomagatchi launched.")

    try:
        run_scanner()
    finally:
        if pet_process.poll() is None:
            pet_process.terminate()
            try:
                pet_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                pet_process.kill()
                pet_process.wait()
        print("Tomagatchi closed.")
