@echo off
cls
REM ============================================================================
REM ==                      Script for Brute-Force Attack                     ==
REM ============================================================================
echo.
echo --- Starting Brute-Force Attack ---
echo.

set VENV_PATH=..\venv
set SCRIPT_PATH=.\bruteforce_attack.py

REM --- Check for venv ---
if not exist "%VENV_PATH%" (
    echo [ERROR] Virtual environment not found at '%VENV_PATH%'.
    echo Please run the 'setup.bat' script from the project root first.
    pause
    exit /b 1
)

echo Activating environment and launching attack...
echo.

REM Activate the virtual environment...
call "%VENV_PATH%\Scripts\activate.bat" && python "%SCRIPT_PATH%"

echo.
echo --- Attack Finished ---
pause