"""
GritX — Desktop Executable Launcher
High-performance desktop runner for GritX Algorithmic Intelligence Engine.
Embeds the official GritX application icon and provides 1-click startup:
1. Configures environment (UTF-8, FFmpeg, Rust audio engine).
2. Verifies Python runtime & virtual environment.
3. Automatically launches the GritX server at http://127.0.0.1:8000.
4. Opens the user's default web browser with live dashboard.
5. Manages server lifecycle and graceful shutdown on exit.
"""
import os
import sys
import time
import socket
import shutil
import signal
import webbrowser
import subprocess
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


def find_app_dir() -> Path:
    """Locates the dsa-tool / gritx application root directory."""
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).parent
    else:
        exe_dir = Path(__file__).resolve().parent

    candidates = [
        exe_dir,
        exe_dir / "dsa-tool",
        exe_dir.parent / "dsa-tool",
        Path.cwd(),
        Path.cwd() / "dsa-tool",
    ]
    for c in candidates:
        if (c / "api_server.py").exists() and (c / "frontend").exists():
            return c.resolve()

    return exe_dir.resolve()


def find_python_interpreter(app_dir: Path) -> Path:
    """Finds the virtual environment Python interpreter."""
    candidates = [
        app_dir / ".venv" / "Scripts" / "python.exe",
        app_dir.parent / ".venv" / "Scripts" / "python.exe",
        app_dir / "venv" / "Scripts" / "python.exe",
        Path(sys.executable),
    ]
    for c in candidates:
        if c.exists() and "pyinstaller" not in c.name.lower():
            return c

    py_cmd = shutil.which("python") or shutil.which("py")
    if py_cmd:
        return Path(py_cmd)

    return Path(sys.executable)


def is_port_listening(host: str = "127.0.0.1", port: int = 8000) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.8):
            return True
    except (socket.error, ConnectionRefusedError, OSError):
        return False


def wait_and_open_browser(host: str = "127.0.0.1", port: int = 8000, timeout: int = 40):
    start = time.time()
    url = f"http://localhost:{port}"
    while time.time() - start < timeout:
        if is_port_listening(host, port):
            time.sleep(0.4)
            print(f"\n[GritX Launcher] Server ready! Opening dashboard: {url}\n")
            if not os.environ.get("NO_BROWSER"):
                import webbrowser
                webbrowser.open(url)
            return True
        time.sleep(0.3)
    return False


def print_banner(app_dir: Path, python_path: Path):
    print("=" * 72)
    print("                      >> GritX Desktop Engine <<")
    print("          Algorithmic Intelligence & Structured Problem Mastery")
    print("=" * 72)
    print(f"  * Application Root:   {app_dir}")
    print(f"  * Python Runtime:     {python_path.name}")
    print(f"  * Web Dashboard:      http://localhost:8000")
    print(f"  * API Docs:           http://localhost:8000/docs")
    print("=" * 72)
    print("  [GritX] Starting background server... (Press Ctrl+C to stop)\n")


def main():
    os.environ["PYTHONUTF8"] = "1"
    os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

    app_dir = find_app_dir()
    python_exe = find_python_interpreter(app_dir)

    # Set up PATH for tools and Rust audio engine
    bin_dir = app_dir / "bin"
    if bin_dir.exists():
        os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")

    print_banner(app_dir, python_exe)

    # Check if server is already running on port 8000
    if is_port_listening("127.0.0.1", 8000):
        print("  [*] An active GritX instance is already running on port 8000.")
        if not os.environ.get("NO_BROWSER"):
            print("  [*] Launching browser directly...\n")
            webbrowser.open("http://localhost:8000")
        return 0

    # Execute startup preflight check if needed
    startup_check = app_dir / "startup_check.py"
    if startup_check.exists():
        try:
            subprocess.run([str(python_exe), str(startup_check)], cwd=str(app_dir), check=False)
        except Exception:
            pass

    # Launch api_server.py
    api_server = app_dir / "api_server.py"
    if not api_server.exists():
        print(f"Error: api_server.py not found at {api_server}")
        input("Press Enter to exit...")
        return 1

    # Start browser opener in background thread
    import threading
    threading.Thread(target=wait_and_open_browser, args=("127.0.0.1", 8000), daemon=True).start()

    # Launch uvicorn server process
    proc = subprocess.Popen(
        [str(python_exe), str(api_server)],
        cwd=str(app_dir)
    )

    try:
        proc.wait()
    except KeyboardInterrupt:
        print("\n[GritX Launcher] Stopping server gracefully...")
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
        print("[GritX Launcher] Stopped.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
