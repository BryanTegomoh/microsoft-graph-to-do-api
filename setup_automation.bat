@echo off
REM Setup Windows Task Scheduler for Daily Automation

echo ===============================================
echo   Task Scheduler Setup
echo ===============================================
echo.
echo This will create a scheduled task to run your
echo daily task brief automatically.
echo.
echo Configuration:
echo - Task Name: ToDoAIDailyBrief
echo - Schedule: Daily at 8:00 AM
echo - Action: Run run_daily.bat
echo.
pause

REM Get the current directory
set SCRIPT_DIR=%~dp0

REM Create the scheduled task
schtasks /Create /TN "ToDoAIDailyBrief" /TR "\"%SCRIPT_DIR%run_daily.bat\"" /SC DAILY /ST 08:00 /F /RL HIGHEST

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Scheduled task created successfully!
    echo.
    echo Task will run daily at 8:00 AM
    echo.
    echo To manage this task:
    echo - Open Task Scheduler (taskschd.msc)
    echo - Look for "ToDoAIDailyBrief"
    echo.
    echo To run manually:
    echo - Double-click run_daily.bat
    echo.
) else (
    echo.
    echo ❌ Failed to create scheduled task
    echo You may need to run this as Administrator
    echo Right-click → Run as administrator
    echo.
)

pause
