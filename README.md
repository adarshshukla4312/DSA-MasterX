# 🚀 DSA Mastery Engine

A full-featured, AI-powered DSA lecture study companion and revision engine. Transform your offline video lectures into searchable transcripts, structured concept ladders, algorithmic flashcards, MCQs, and personalized LeetCode problem recommendations.

---

## ⚡ 1-Click Quickstart (Run on Any Computer)

This app is pre-configured to work **right out of the box** without any complex manual installation.

### Step 1: Clone Repository
```bash
git clone https://github.com/adarshshukla4312/dsa-mastery-engine.git
cd dsa-mastery-engine
```

### Step 2: Run Launcher
- **On Windows**: Double-click **`start.bat`** (or run `.\start.bat` in PowerShell).
- **On Linux / macOS**: Run `./start.sh` in Terminal.

### What Happens Automatically at Startup:
1. **Python Detection**: Automatically detects Python 3.10+ (or Windows Python launcher `py`).
2. **Virtual Environment**: Automatically builds a local `.venv` isolation environment.
3. **Dependencies**: Automatically verifies and installs all required packages (`fastapi`, `uvicorn`, `faster-whisper`, etc.).
4. **Lecture Folder Selection**: An interactive prompt allows you to choose where your DSA videos are stored (you can also change this anytime directly in the web app).
5. **Speech AI Model**: Automatically checks and pre-downloads the Whisper speech-to-text model (`small`, ~480MB) so audio transcription works reliably offline.
6. **FFmpeg**: Checks for audio extraction capabilities and offers automatic WinGet installation if missing.
7. **Instant Browser Launch**: Starts the engine at `http://localhost:8000` and automatically opens your browser.

---

## 📁 Setting or Changing Lecture Directory

You can point the app to your DSA lecture videos folder:
1. **During First Startup**: You will be prompted to choose the folder or paste its path.
2. **Inside the Web App**: Go to the **Lecture Library** tab in your browser and click **Change Folder** to choose or paste any folder path on your computer.
3. **Via `.env` file**: Open `dsa-tool/.env` and set:
   ```env
   LECTURE_DIR=D:\Courses\Java DSA
   ```

Supported video formats: `.mp4`, `.mkv`, `.avi`, `.mov`, `.webm`.

---

## 🧠 Core Features

- **Automated Video-to-Text Pipeline**:
  - High-accuracy audio transcription via `faster-whisper` (GPU CUDA accelerated with seamless CPU fallback).
  - Audio chunking for low-RAM usage on standard laptops.
- **AI Concept Extraction**:
  - Automatically identifies topics, algorithmic techniques, code snippets, and key lecture timestamps.
- **Problem Bank & Smart Matching**:
  - Integrated 600+ LeetCode problem database with difficulty ratings, pattern tags, and prerequisites.
  - Automatically maps lecture discussions to curated coding challenges.
- **Active Recall & Spaced Repetition**:
  - Synthesizes flashcards and MCQs directly from each lecture.
  - Built-in SuperMemo SM-2 spaced repetition scheduler to optimize long-term retention.
- **Modern Responsive Web UI**:
  - Fast single-page application built with FastAPI and vanilla JavaScript with dark glassmorphic styling.

---

## 🛠️ Manual Run / Developer Mode

If you prefer to run the backend manually:

```bash
cd dsa-tool
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python startup_check.py
python api_server.py
```

Then visit [http://localhost:8000](http://localhost:8000) in your browser.

---

## ⚙️ Configuration (`.env`)

Default working NVIDIA API keys are provided in `.env.example`. You can customize them if desired:

```env
# NVIDIA NIM API Keys (optional overrides)
NVIDIA_STANDARD_API_KEY=nvapi-...
NVIDIA_REASONING_API_KEY=nvapi-...

# Videos path
LECTURE_DIR=C:\Your\Path\To\Lectures
```

---

## 📄 License
Private project.
