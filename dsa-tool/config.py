"""
DSA Mastery Tool — Configuration
"""
import os
import sys
import shutil
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ─── Ensure FFmpeg is in PATH ────────────────────────────────────────────────
if not shutil.which("ffmpeg"):
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    if local_appdata:
        winget_links = Path(local_appdata) / "Microsoft" / "WinGet" / "Links"
        if winget_links.exists():
            os.environ["PATH"] = str(winget_links) + os.pathsep + os.environ.get("PATH", "")

    if not shutil.which("ffmpeg") and local_appdata:
        winget_packages = Path(local_appdata) / "Microsoft" / "WinGet" / "Packages"
        if winget_packages.exists():
            for ffmpeg_exe in winget_packages.glob("**/ffmpeg.exe"):
                os.environ["PATH"] = str(ffmpeg_exe.parent) + os.pathsep + os.environ.get("PATH", "")
                break

# ─── Add NVIDIA CUDA DLLs (cublas, cudnn) to PATH for GPU Acceleration ──────
for p in sys.path:
    if "site-packages" in p:
        nvidia_dir = Path(p) / "nvidia"
        if nvidia_dir.exists():
            for bin_dir in nvidia_dir.glob("**/bin"):
                os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.resolve()

# ─── Ensure local tools / bin are in PATH for FFmpeg ─────────────────────────
if not shutil.which("ffmpeg"):
    for cand in [BASE_DIR / "tools", BASE_DIR / "bin", BASE_DIR.parent / "tools", BASE_DIR.parent / "bin"]:
        if (cand / "ffmpeg.exe").exists():
            os.environ["PATH"] = str(cand) + os.pathsep + os.environ.get("PATH", "")
            break

def _resolve_lecture_dir() -> Path:
    # 1. Check environment variable
    env_dir = os.getenv("LECTURE_DIR")
    if env_dir:
        p = Path(env_dir)
        if p.exists():
            return p

    # 2. Check candidate directories for presence of video files or directory existence
    candidates = [
        Path(r"C:\Java DSA"),
        BASE_DIR.parent.parent,
        BASE_DIR.parent,
        Path(r"d:\Cources\Java DSA"),
    ]
    for c in candidates:
        if c.exists() and c.is_dir():
            for ext in {".mp4", ".mkv", ".avi", ".mov", ".webm"}:
                if list(c.glob(f"*{ext}")):
                    return c

    for c in candidates:
        if c.exists() and c.is_dir():
            return c

    return BASE_DIR.parent

LECTURE_DIR = _resolve_lecture_dir()

def update_lecture_dir(new_path: str | Path) -> Path:
    """Updates LECTURE_DIR at runtime and persists it into .env."""
    global LECTURE_DIR
    p = Path(new_path).resolve()
    LECTURE_DIR = p
    os.environ["LECTURE_DIR"] = str(p)

    env_file = BASE_DIR / ".env"
    lines = []
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

    found = False
    new_lines = []
    for line in lines:
        if line.strip().startswith("LECTURE_DIR="):
            new_lines.append(f"LECTURE_DIR={str(p)}\n")
            found = True
        else:
            new_lines.append(line)
    if not found:
        new_lines.append(f"LECTURE_DIR={str(p)}\n")

    with open(env_file, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    return p

DATA_DIR = BASE_DIR / "data"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"
AUDIO_DIR = DATA_DIR / "audio"
DB_PATH = DATA_DIR / "dsa_tool.db"
PROBLEMS_JSON = DATA_DIR / "problems.json"
LOG_FILE_PATH = DATA_DIR / "dsa_tool.log"

# Create directories
for d in [DATA_DIR, TRANSCRIPTS_DIR, AUDIO_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ─── Logging Setup ────────────────────────────────────────────────────────────
def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
        file_handler = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

setup_logging()

def get_hardware_status() -> dict:
    """Detects if CTranslate2 GPU (CUDA) hardware acceleration is available."""
    try:
        import ctranslate2
        count = ctranslate2.get_cuda_device_count()
        if count > 0:
            return {
                "device": "cuda",
                "label": "🚀 GPU Accelerated (NVIDIA CUDA float16)",
                "is_gpu": True
            }
    except Exception:
        pass
        
    return {
        "device": "cpu",
        "label": "💻 CPU Mode (int8 fallback)",
        "is_gpu": False
    }

# ─── LLM Configuration (Dual-Model Nemotron Architecture) ────────────────────
LLM_BASE_URL = "https://integrate.api.nvidia.com/v1"

# Standard Model — Fast extraction, structured output, JSON adherence
LLM_STANDARD_API_KEY = os.getenv("NVIDIA_STANDARD_API_KEY", "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")
LLM_STANDARD_MODEL = "mistralai/mistral-nemotron"

# Reasoning Model — Deep algorithmic thinking, curriculum design, MCQs
LLM_REASONING_API_KEY = os.getenv("NVIDIA_REASONING_API_KEY", "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")
LLM_REASONING_MODEL = "nvidia/nemotron-3-ultra-550b-a55b"

# Backward compatibility aliases
LLM_API_KEY = LLM_STANDARD_API_KEY
LLM_MODEL = LLM_STANDARD_MODEL

LLM_TEMPERATURE = 0.7
LLM_TOP_P = 0.95
LLM_MAX_TOKENS = 16384
LLM_THINKING = True
LLM_REASONING_EFFORT = "high"

# ─── Whisper ──────────────────────────────────────────────────────────────────
WHISPER_MODEL = "small"
WHISPER_DEVICE = "cuda"  # Falls back to "cpu" if CUDA unavailable
WHISPER_COMPUTE_TYPE = "float16"

# ─── Recommendation ──────────────────────────────────────────────────────────
RECOMMEND_EASY = 2
RECOMMEND_MEDIUM = 2
RECOMMEND_HARD = 1

# ─── Video file extensions to scan ───────────────────────────────────────────
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".webm"}
