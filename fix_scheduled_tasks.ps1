# Fix Scheduled Tasks for ToDoAI
# Run this script as Administrator

$taskPath = "c:\Users\bryan\OneDrive\Documents\xAI - Medicine\microsoft-graph-to-do-api"
$dailyBat = "$taskPath\run_daily.bat"
$weeklyBat = "$taskPath\run_weekly.bat"

# Common settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)

$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited

# ==================== DAILY TASKS ====================
Write-Host "=== Fixing Daily Tasks ===" -ForegroundColor Cyan

# Delete existing daily tasks
Write-Host "Deleting existing daily tasks..." -ForegroundColor Yellow
$dailyTasks = @("ToDoAI_MorningBrief", "ToDoAI_AfternoonBrief", "ToDoAI_EveningBrief")
foreach ($task in $dailyTasks) {
    try {
        Unregister-ScheduledTask -TaskName $task -Confirm:$false -ErrorAction SilentlyContinue
        Write-Host "  Deleted: $task" -ForegroundColor Gray
    } catch {
        Write-Host "  Task not found: $task" -ForegroundColor Gray
    }
}

$dailyAction = New-ScheduledTaskAction `
    -Execute $dailyBat `
    -WorkingDirectory $taskPath

# Morning Brief - 8:00 AM
$triggerMorning = New-ScheduledTaskTrigger -Daily -At "08:00"
Register-ScheduledTask `
    -TaskName "ToDoAI_MorningBrief" `
    -Action $dailyAction `
    -Trigger $triggerMorning `
    -Settings $settings `
    -Principal $principal `
    -Description "ToDoAI Morning Brief - sends daily task summary email"
Write-Host "  Created: ToDoAI_MorningBrief (8:00 AM)" -ForegroundColor Green

# Afternoon Brief - 2:00 PM
$triggerAfternoon = New-ScheduledTaskTrigger -Daily -At "14:00"
Register-ScheduledTask `
    -TaskName "ToDoAI_AfternoonBrief" `
    -Action $dailyAction `
    -Trigger $triggerAfternoon `
    -Settings $settings `
    -Principal $principal `
    -Description "ToDoAI Afternoon Brief - sends daily task summary email"
Write-Host "  Created: ToDoAI_AfternoonBrief (2:00 PM)" -ForegroundColor Green

# Evening Brief - 8:00 PM
$triggerEvening = New-ScheduledTaskTrigger -Daily -At "20:00"
Register-ScheduledTask `
    -TaskName "ToDoAI_EveningBrief" `
    -Action $dailyAction `
    -Trigger $triggerEvening `
    -Settings $settings `
    -Principal $principal `
    -Description "ToDoAI Evening Brief - sends daily task summary email"
Write-Host "  Created: ToDoAI_EveningBrief (8:00 PM)" -ForegroundColor Green

# ==================== WEEKLY TASKS ====================
Write-Host "`n=== Fixing Weekly Tasks ===" -ForegroundColor Cyan

# Delete existing weekly tasks
Write-Host "Deleting existing weekly tasks..." -ForegroundColor Yellow
$weeklyTasks = @("ToDoAI_WeeklySunday", "ToDoAI_WeeklyWednesday", "ToDoAI_WeeklyFriday")
foreach ($task in $weeklyTasks) {
    try {
        Unregister-ScheduledTask -TaskName $task -Confirm:$false -ErrorAction SilentlyContinue
        Write-Host "  Deleted: $task" -ForegroundColor Gray
    } catch {
        Write-Host "  Task not found: $task" -ForegroundColor Gray
    }
}

$weeklyAction = New-ScheduledTaskAction `
    -Execute $weeklyBat `
    -WorkingDirectory $taskPath

# Weekly Sunday - 8:00 PM
$triggerSunday = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At "20:00"
Register-ScheduledTask `
    -TaskName "ToDoAI_WeeklySunday" `
    -Action $weeklyAction `
    -Trigger $triggerSunday `
    -Settings $settings `
    -Principal $principal `
    -Description "ToDoAI Weekly Report - Sunday evening planning"
Write-Host "  Created: ToDoAI_WeeklySunday (Sunday 8:00 PM)" -ForegroundColor Green

# Weekly Wednesday - 8:00 AM
$triggerWednesday = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Wednesday -At "08:00"
Register-ScheduledTask `
    -TaskName "ToDoAI_WeeklyWednesday" `
    -Action $weeklyAction `
    -Trigger $triggerWednesday `
    -Settings $settings `
    -Principal $principal `
    -Description "ToDoAI Weekly Report - Wednesday midweek review"
Write-Host "  Created: ToDoAI_WeeklyWednesday (Wednesday 8:00 AM)" -ForegroundColor Green

# Weekly Friday - 5:00 PM
$triggerFriday = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Friday -At "17:00"
Register-ScheduledTask `
    -TaskName "ToDoAI_WeeklyFriday" `
    -Action $weeklyAction `
    -Trigger $triggerFriday `
    -Settings $settings `
    -Principal $principal `
    -Description "ToDoAI Weekly Report - Friday wrap-up"
Write-Host "  Created: ToDoAI_WeeklyFriday (Friday 5:00 PM)" -ForegroundColor Green

# ==================== SUMMARY ====================
Write-Host "`n=== Settings Applied ===" -ForegroundColor Cyan
Write-Host "  - Working directory: $taskPath" -ForegroundColor White
Write-Host "  - Runs on battery power" -ForegroundColor White
Write-Host "  - Won't stop if switching to battery" -ForegroundColor White
Write-Host "  - Starts when available (if missed)" -ForegroundColor White

Write-Host "`nVerifying all tasks..." -ForegroundColor Yellow
Get-ScheduledTask -TaskName "ToDoAI_*" | Format-Table TaskName, State, @{N='NextRun';E={(Get-ScheduledTaskInfo -TaskName $_.TaskName).NextRunTime}}
