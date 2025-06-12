@echo off
cls
REM ============================================================================
REM == Batch Script for P2P Encrypted Chat                                    ==
REM == 1. Check if the 'venv' directory exists.                               ==
REM == 2. Activate the virtual environment.                                   ==
REM == 3. Run the main 'launcher.py' script.                                  ==
REM ==                                                                        ==
REM == Press Ctrl+C in this window to shut down                               ==
REM ============================================================================
echo.
echo --- Starting P2P Encrypted Chat Demo ---
echo.

REM --- Step 1: Verify that the setup has been run ---
echo [1/2] Checking for virtual environment...
if not exist "venv" (
    echo [ERROR] Virtual environment 'venv' not found.
    echo Please run the 'setup.bat' script first to install all dependencies.
    echo.
    pause
    exit /b 1
)
echo      - Virtual environment found.
echo.

REM --- Step 2: Activate venv and run the launcher ---
echo [2/2] Activating environment and starting the launcher...
echo      - If the demo does not start, please ensure you have run 'setup.bat' successfully.
echo      - The backend and frontend servers will start in the background.
echo      - Two Chrome browser windows will open automatically after about 10-15 seconds.
echo.
echo ======================================================================
echo ==           PRESS CTRL+C IN THIS WINDOW TO STOP THE DEMO           ==
echo ======================================================================
echo.

REM Activate the virtual environment and run the launcher in one line
call "venv\Scripts\activate.bat" && python "launcher.py"

REM The 'call' command passes control and the '&&' ensures the second command
REM only runs if the first one is successful. The launcher.py script contains
REM the main loop, so this batch file will wait here until you press Ctrl+C
REM in launcher.py's process tree.