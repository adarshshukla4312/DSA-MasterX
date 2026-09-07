"""
DSA Mastery Engine — Startup Environment & Preflight Check
Handles out-of-the-box configuration on fresh machines:
1. Environment initialization (.env from .env.example)
2. Interactive lecture directory selection
3. FFmpeg verification & helper
4. Whisper AI speech-to-text model verification & pre-download
5. Database schema initialization & problem bank loading
"""
import os
import sys
import shutil
import urllib.request
import zipfile
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / "data"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"
AUDIO_DIR = DATA_DIR / "audio"
DB_PATH = DATA_DIR / "dsa_tool.db"
PROBLEMS_JSON = DATA_DIR / "problems.json"
TOOLS_DIR = BASE_DIR / "tools"

def print_header():
    print("=" * 70)
    print("           DSA Mastery Engine — Preflight Startup Check")
    print("=" * 70)

def ensure_env_file():
    env_file = BASE_DIR / ".env"
    example_file = BASE_DIR / ".env.example"
    if not env_file.exists():
        if example_file.exists():
            shutil.copy(example_file, env_file)
            print("[OK] Initialized default .env configuration file.")
        else:
            env_file.write_text("LECTURE_DIR=\n", encoding="utf-8")
            print("[OK] Created blank .env configuration file.")

def prompt_lecture_directory():
    env_file = BASE_DIR / ".env"
    from dotenv import load_dotenv
    load_dotenv(env_file)
    current_dir = os.getenv("LECTURE_DIR", "").strip()

    if current_dir and Path(current_dir).exists() and Path(current_dir).is_dir():
        print(f"[OK] Lecture directory configured: {current_dir}")
        return

    print("\n[?] DSA Lecture Video Directory Not Configured")
    print("    You can select where your DSA lecture videos (.mp4, .mkv) are stored.")
    
    chosen_path = ""
    # Try GUI picker first
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        selected = filedialog.askdirectory(title="Select DSA Video Lectures Folder")
        root.destroy()
        if selected and os.path.exists(selected):
            chosen_path = selected
    except Exception:
        pass

    # If GUI was cancelled or failed, ask on console with timeout/skip option
    if not chosen_path:
        print("    (You can also configure or change this anytime inside the Web App)")
        try:
            val = input("    Enter full folder path [Press Enter to skip]: ").strip().strip('"').strip("'")
            if val and os.path.exists(val):
                chosen_path = val
        except (EOFError, KeyboardInterrupt):
            pass

    if chosen_path:
        # Update .env
        from config import update_lecture_dir
        update_lecture_dir(chosen_path)
        print(f"[OK] Saved lecture directory: {chosen_path}")
    else:
        print("[i] Skipping folder configuration for now. You can set it later in the Library tab.")

def ensure_ffmpeg():
    # 1. Check PATH
    if shutil.which("ffmpeg"):
        print("[OK] FFmpeg is installed and available in PATH.")
        return

    # 2. Check local tools directory
    local_ffmpeg = TOOLS_DIR / "ffmpeg.exe"
    if local_ffmpeg.exists():
        os.environ["PATH"] = str(TOOLS_DIR) + os.pathsep + os.environ.get("PATH", "")
        print(f"[OK] FFmpeg found in local tools: {TOOLS_DIR}")
        return

    # 3. Check WinGet installations
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    if local_appdata:
        winget_links = Path(local_appdata) / "Microsoft" / "WinGet" / "Links"
        if (winget_links / "ffmpeg.exe").exists():
            os.environ["PATH"] = str(winget_links) + os.pathsep + os.environ.get("PATH", "")
            print("[OK] FFmpeg found in WinGet links.")
            return

    print("\n[!] FFmpeg was not detected in PATH.")
    print("    FFmpeg is required to extract audio from lecture videos.")
    
    # Try auto-install via winget if on Windows
    if sys.platform == "win32" and shutil.which("winget"):
        print("    Attempting automatic installation via winget...")
        import subprocess
        try:
            res = subprocess.run(
                ["winget", "install", "Gyan.FFmpeg", "--accept-source-agreements", "--accept-package-agreements", "--silent"],
                capture_output=True, text=True, timeout=120
            )
            if res.returncode == 0 or shutil.which("ffmpeg"):
                print("[OK] FFmpeg installed successfully via WinGet!")
                return
        except Exception as e:
            print(f"    Auto-install note: {e}")

    print("    TIP: You can install FFmpeg anytime by running: winget install Gyan.FFmpeg")

def ensure_whisper_model():
    from config import WHISPER_MODEL
    print(f"\n[*] Verifying speech-to-text model ('{WHISPER_MODEL}')...")
    try:
        from faster_whisper.utils import download_model
        print(f"    Checking / downloading faster-whisper '{WHISPER_MODEL}' model weights...")
        print("    (If this is the first startup, this downloads ~480MB once so transcription works offline)")
        model_path = download_model(WHISPER_MODEL)
        print(f"[OK] Speech-to-text model verified at: {model_path}")
    except Exception as e:
        print(f"[WARNING] Whisper model pre-download encountered an issue: {e}")
        print("          The model will attempt to download automatically when transcription is first started.")

def ensure_database():
    for d in [DATA_DIR, TRANSCRIPTS_DIR, AUDIO_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    from db.schema import init_db, load_problems_from_json
    init_db(DB_PATH)
    if PROBLEMS_JSON.exists():
        count = load_problems_from_json(DB_PATH, PROBLEMS_JSON)
        if count > 0:
            print(f"[OK] Initialized database with {count} problems.")
        else:
            print("[OK] Database schema verified.")
    else:
        print("[OK] Database schema verified.")

def main():
    print_header()
    ensure_env_file()
    prompt_lecture_directory()
    ensure_ffmpeg()
    ensure_whisper_model()
    ensure_database()
    print("\n" + "=" * 70)
    print(" [READY] Preflight check completed successfully! Launching app...")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
