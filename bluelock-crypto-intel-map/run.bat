@echo off
title BlueLock Crypto Intel Dashboard
color 0A

echo.
echo  ============================================================
echo   BLUELOCK CRYPTO INTEL DASHBOARD
echo   Defensive Public-Chain Forensics Platform
echo  ============================================================
echo.

REM Always run from this folder
cd /d "%~dp0"

REM ── 1. Check Python ──────────────────────────────────────────
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python was not found on your system.
    echo.
    echo  Please install Python 3.11 or newer from:
    echo    https://www.python.org/downloads/
    echo.
    echo  IMPORTANT: During installation, check:
    echo    "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo  [OK] Python %PYVER% detected.

REM ── 2. Create virtual environment if missing ─────────────────
if not exist ".venv\" (
    echo  [SETUP] Creating virtual environment in .venv ...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo  [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo  [OK] Virtual environment created.
)

REM ── 3. Activate virtual environment ──────────────────────────
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo  [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)
echo  [OK] Virtual environment activated.

REM ── 4. Upgrade pip tooling ───────────────────────────────────
echo  [SETUP] Updating pip tooling ...
python -m pip install --upgrade pip setuptools wheel --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo  [ERROR] Failed to upgrade pip tooling.
    pause
    exit /b 1
)

REM ── 5. Install requirements ───────────────────────────────────
echo  [SETUP] Installing / verifying dependencies ...
python -m pip install -r requirements.txt --prefer-binary --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo  [ERROR] Dependency installation failed.
    echo.
    echo  If you updated from an older ZIP, delete the .venv folder and run this again.
    echo.
    pause
    exit /b 1
)
echo  [OK] Dependencies ready.

REM ── 6. Copy .env if missing ───────────────────────────────────
if not exist ".env" (
    copy .env.example .env >nul
    echo  [SETUP] Created .env from .env.example
    echo  [INFO]  Add your Etherscan V2 API key to ETHERSCAN_API_KEY.
)

REM ── 7. Ensure data directory exists ──────────────────────────
if not exist "data\" mkdir data
if not exist "reports\" mkdir reports

REM ── 8. Open browser after server starts ──────────────────────
echo  [INFO] Starting server at http://127.0.0.1:8000 ...
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:8000"

REM ── 9. Start FastAPI server ───────────────────────────────────
echo.
echo  ============================================================
echo   Server running at: http://127.0.0.1:8000
echo   Press CTRL+C to stop.
echo  ============================================================
echo.
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

echo.
echo  [INFO] Server stopped.
pause
