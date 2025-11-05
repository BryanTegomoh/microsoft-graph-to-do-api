@echo off
REM Daily Task Brief Runner for Windows
REM This script activates the virtual environment and runs the task manager

echo ===============================================
echo   Microsoft To Do AI Task Manager
echo ===============================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Run the main script
python main.py

REM Deactivate virtual environment
deactivate

echo.
echo ===============================================
echo   Task Brief Complete
echo ===============================================
echo.

REM Pause to see output (remove this line for scheduled tasks)
pause
