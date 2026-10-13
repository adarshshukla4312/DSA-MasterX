@echo off
setlocal
title DSA Mastery Engine
color 0A
cls

echo =======================================================================
echo                   DSA Mastery Engine (Launcher)
echo =======================================================================
echo.

:: 1. Navigate to tool directory
cd /d "%~dp0"
if exist "dsa-tool" cd /d "%~dp0dsa-tool"

:: 2. Detect Python
set "PYTHON_CMD="
where py >nul 2>&1
if %ERRORLEVEL% equ 0 (
    py -3.11 -c "exit(0)" >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        set "PYTHON_CMD=py -3.11"
        goto :python_found
    )
    py -3.12 -c "exit(0)" >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        set "PYTHON_CMD=py -3.12"
        goto :python_found
    )
)

where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PYTHON_CMD=python"
    goto :python_found
)

where py >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PYTHON_CMD=py -3"
    goto :python_found
)

:: Python not found
color 0C
echo [ERROR] Python was not found on your computer.
echo.
echo Please install Python 3.10 or higher from:
echo https://www.python.org/downloads/
echo Note: Make sure to check Add Python to PATH during installation.
echo.
echo Or if you have Windows Package Manager, run:
echo winget install Python.Python.3.11
echo.
pause
exit /b 1

:python_found
echo [*] Detected Python: %PYTHON_CMD%

:: 3. Check / Create Virtual Environment (.venv)
if not exist ".venv" goto :create_venv
set "VENV_PYTHON=.venv\Scripts\python.exe"
if exist "%VENV_PYTHON%" goto :venv_ready

:create_venv
echo [*] Setting up virtual environment (.venv)...
%PYTHON_CMD% -m venv --system-site-packages .venv
if %ERRORLEVEL% neq 0 (
    echo [!] Warning: Failed to create .venv. Falling back to global Python.
    set "VENV_PYTHON=%PYTHON_CMD%"
    goto :venv_ready
)
set "VENV_PYTHON=.venv\Scripts\python.exe"
if not exist "%VENV_PYTHON%" set "VENV_PYTHON=%PYTHON_CMD%"
echo [OK] Virtual environment created.

:venv_ready
:: 4. Verify & Install Requirements
echo [*] Verifying dependencies...
%VENV_PYTHON% -c "import fastapi, uvicorn, pydantic, dotenv" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [OK] Dependencies verified.
    goto :deps_ready
)

echo [*] Installing required packages (one-time setup)...
%VENV_PYTHON% -m pip install --upgrade pip --quiet
%VENV_PYTHON% -m pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    color 0C
    echo [ERROR] Failed to install dependencies. Check your internet connection.
    pause
    exit /b 1
)
echo [OK] All dependencies installed.

:deps_ready
:: 5. Run Preflight Startup Check (config, lecture directory, ffmpeg, models, db)
echo.
set PYTHONUTF8=1
set HF_HUB_DISABLE_SYMLINKS_WARNING=1
set OMP_NUM_THREADS=12
set MKL_NUM_THREADS=12
%VENV_PYTHON% startup_check.py
if %ERRORLEVEL% neq 0 (
    echo [!] Preflight check exited with warnings. Attempting to start server...
)

:: 6. Start the API & Web App Server
echo.
echo =======================================================================
echo  Server starting... The browser will automatically open shortly.
echo  Press Ctrl+C in this window to stop the server.
echo =======================================================================
echo.

%VENV_PYTHON% api_server.py

pause
