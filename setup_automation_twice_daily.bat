@echo off
REM Setup Windows Task Scheduler for TWICE DAILY Automation

echo ===============================================
echo   Task Scheduler Setup - TWICE DAILY
echo ===============================================
echo.
echo This will create TWO scheduled tasks:
echo - Morning Brief: Daily at 8:00 AM
echo - Afternoon Brief: Daily at 2:00 PM
echo.
pause

REM Get the current directory
set SCRIPT_DIR=%~dp0

echo.
echo Creating MORNING task (8:00 AM)...
schtasks /Create /TN "ToDoAI_MorningBrief" /TR "\"%SCRIPT_DIR%run_daily.bat\"" /SC DAILY /ST 08:00 /F /RL HIGHEST

if %ERRORLEVEL% EQU 0 (
    echo ✓ Morning task created successfully!
) else (
    echo ✗ Failed to create morning task
)

echo.
echo Creating AFTERNOON task (2:00 PM)...
schtasks /Create /TN "ToDoAI_AfternoonBrief" /TR "\"%SCRIPT_DIR%run_daily.bat\"" /SC DAILY /ST 14:00 /F /RL HIGHEST

if %ERRORLEVEL% EQU 0 (
    echo ✓ Afternoon task created successfully!
) else (
    echo ✗ Failed to create afternoon task
)

echo.
echo ===============================================
echo   Setup Complete!
echo ===============================================
echo.
echo Tasks created:
echo - ToDoAI_MorningBrief (8:00 AM daily)
echo - ToDoAI_AfternoonBrief (2:00 PM daily)
echo.
echo To manage:
echo - Open Task Scheduler (taskschd.msc)
echo - Find tasks under "Task Scheduler Library"
echo.
echo To run manually:
echo - Double-click run_daily.bat
echo.
pause
