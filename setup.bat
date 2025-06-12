@echo off
setlocal
cls
REM ============================================================================
REM == Setup Script for P2P Secure Encrypted Chat Project                     ==
REM == 1. Create a Python virtual environment.                                ==
REM == 2. Install Python dependencies from backend/requirements.txt.          ==
REM == 3. Install Node.js dependencies from frontend/package.json.            ==
REM ============================================================================
echo.
echo --- P2P Chat Project Setup ---
echo.

REM --- 1. Check for prerequisites ---
echo [1/4] Checking for Python and Node.js...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    GOTO:Error
)
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not in your PATH.
    GOTO:Error
)
echo      - Python found.
echo      - Node.js found.
echo.

REM --- 2. Create Python virtual environment ---
echo [2/4] Setting up Python virtual environment...
if not exist ".venv" (
    echo      - Creating virtual environment '.venv'...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        GOTO:Error
    )
) else (
    echo      - Virtual environment '.venv' already exists.
)
echo.

REM --- 3. Install Python dependencies ---
echo [3/4] Installing Python dependencies from backend/requirements.txt...
call ".venv\Scripts\python.exe" -m pip install -r "backend\requirements.txt"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Python dependencies. Please check for errors above.
    GOTO:Error
)
echo      - Python dependencies installed successfully.
echo.

REM --- 4. Install Node.js dependencies ---
echo [4/4] Installing Node.js dependencies in 'frontend' directory...
pushd "frontend"
call npm install
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Node.js dependencies. Please check for errors above.
    popd
    GOTO:Error
)
popd
echo      - Node.js dependencies installed successfully.
echo.

GOTO:Success

:Error
echo.
echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
echo !!      SETUP FAILED              !!
echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
echo.
pause
exit /b 1

:Success
echo.
echo =========================================
echo ==           SETUP COMPLETE            ==
echo =========================================
echo You can now run the application using the launcher.
echo.
echo To run the demo, open a NEW terminal, navigate to this directory, and then run:
echo.
echo   1. Activate environment: venv\Scripts\activate
echo   2. Run launcher:        python launcher.py
echo.
pause
exit /b 0