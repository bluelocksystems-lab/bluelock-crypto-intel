@echo off
title BlueLock Setup
color 0B

echo.
echo  ============================================================
echo   BLUELOCK CRYPTO INTEL - SETUP
echo  ============================================================
echo.

cd /d "%~dp0"

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python not found. Install Python 3.11+ from https://python.org
    echo  Make sure to check "Add Python to PATH".
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo  [OK] Python %PYVER%

if not exist ".venv\" (
    echo  [SETUP] Creating .venv ...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo  [ERROR] Failed to create .venv.
        pause
        exit /b 1
    )
)

call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo  [ERROR] Failed to activate .venv.
    pause
    exit /b 1
)

echo  [SETUP] Updating pip tooling ...
python -m pip install --upgrade pip setuptools wheel --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo  [ERROR] Failed to update pip tooling.
    pause
    exit /b 1
)

echo  [SETUP] Installing requirements ...
python -m pip install -r requirements.txt --prefer-binary --disable-pip-version-check
if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Requirement install failed.
    echo  If this is an older virtual environment, delete .venv and run install.bat again.
    echo.
    pause
    exit /b 1
)

if not exist ".env" (
    copy .env.example .env >nul
    echo  [SETUP] Created .env - add your Etherscan V2 API key before running.
)

if not exist "data\" mkdir data
if not exist "reports\" mkdir reports

echo.
echo  [DONE] Setup complete. Run run.bat to start the dashboard.
pause
