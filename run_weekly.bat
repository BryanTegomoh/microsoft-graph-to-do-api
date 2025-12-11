@echo off
REM Weekly Task Brief Runner for Windows
REM This script activates the virtual environment and runs the weekly report

REM Change to script directory
cd /d "%~dp0"

REM Log start time
echo [%date% %time%] Starting weekly report... >> output\task_manager.log

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Run the main script with force-weekly flag and log output
python main.py --force-weekly >> output\task_manager.log 2>&1

REM Deactivate virtual environment
deactivate

REM Log completion
echo [%date% %time%] Weekly report complete. >> output\task_manager.log
