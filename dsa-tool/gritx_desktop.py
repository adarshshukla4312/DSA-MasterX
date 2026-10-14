"""
GritX — Desktop Executable Launcher
Starts the GritX algorithmic intelligence engine, initializes preflight checks,
serves the FastAPI UI at http://127.0.0.1:8000, and launches the desktop browser.
"""
import os
import sys
import time
import socket
import webbrowser
import threading
from pathlib import Path

# Ensure UTF-8 output on Windows
os.environ["PYTHONUTF8"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Determine application base directory (support PyInstaller bundled mode & normal mode)
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    BUNDLE_DIR = Path(sys._MEIPASS)
    APP_DIR = Path(sys.executable).parent
else:
    BUNDLE_DIR = Path(__file__).resolve().parent
    APP_DIR = BUNDLE_DIR

# Ensure APP_DIR and BUNDLE_DIR are in Python path
for p in [str(BUNDLE_DIR), str(APP_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Also ensure parent directory is accessible if run from repo root
parent_dir = APP_DIR.parent
if (parent_dir / "dsa-tool").exists() and str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))


def print_banner(host: str, port: int):
    print("=" * 72)
    print("                      ⚡ GritX Desktop Engine ⚡")
    print("          Algorithmic Intelligence & Structured Problem Mastery")
    print("=" * 72)
    print(f"  • Web Dashboard:       http://localhost:{port}")
    print(f"  • API Documentation:   http://localhost:{port}/docs")
    print(f"  • Base Directory:      {APP_DIR}")
    print("=" * 72)
    print("  [GritX] Engine active. Press Ctrl+C in this console to stop.\n")


def open_browser_when_ready(host: str = "127.0.0.1", port: int = 8000, timeout: int = 30):
    """Waits for port to accept connections, then opens user's browser."""
    def _worker():
        if os.environ.get("NO_BROWSER"):
            return
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                with socket.create_connection((host, port), timeout=1):
                    time.sleep(0.5)
                    url = f"http://localhost:{port}"
                    print(f"  [*] Server responded. Launching browser at {url} ...\n")
                    webbrowser.open(url)
                    return
            except (socket.error, ConnectionRefusedError, OSError):
                time.sleep(0.4)
    threading.Thread(target=_worker, daemon=True).start()


def main():
    # 1. Preflight database and schema verification
    try:
        from db.schema import init_db, load_problems_from_json
        from config import DB_PATH, PROBLEMS_JSON
        init_db(DB_PATH)
        if PROBLEMS_JSON.exists():
            load_problems_from_json(DB_PATH, PROBLEMS_JSON)
    except Exception as e:
        print(f"  [Warning] Preflight DB check note: {e}")

    # 2. Start browser launcher in background
    port = 8000
    print_banner("127.0.0.1", port)
    open_browser_when_ready("127.0.0.1", port)

    # 3. Run Uvicorn server
    import uvicorn
    from api_server import app

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=False
    )


if __name__ == "__main__":
    main()
