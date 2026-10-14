#!/usr/bin/env bash
set -e

echo "======================================================================="
echo "                               GritX (Launcher)"
echo "======================================================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -d "$SCRIPT_DIR/dsa-tool" ]; then
    cd "$SCRIPT_DIR/dsa-tool"
else
    cd "$SCRIPT_DIR"
fi

PYTHON_CMD=""
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "[ERROR] Python 3 was not found. Please install Python 3.10+."
    exit 1
fi

if [ ! -d ".venv" ]; then
    echo "[*] Creating virtual environment (.venv)..."
    $PYTHON_CMD -m venv .venv
fi

VENV_PYTHON=".venv/bin/python"
if [ ! -f "$VENV_PYTHON" ]; then
    VENV_PYTHON="$PYTHON_CMD"
fi

echo "[*] Verifying dependencies..."
if ! $VENV_PYTHON -c "import fastapi, uvicorn, faster_whisper, openai, pydantic, rich, dotenv" &>/dev/null; then
    echo "[*] Installing dependencies..."
    $VENV_PYTHON -m pip install --upgrade pip --quiet
    $VENV_PYTHON -m pip install -r requirements.txt
fi

export PYTHONUTF8=1
$VENV_PYTHON startup_check.py

echo "[*] Starting GritX server..."
$VENV_PYTHON api_server.py
