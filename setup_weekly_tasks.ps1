# Setup Weekly Scheduled Tasks with proper working directory
$workingDir = "c:\Users\bryan\OneDrive\Documents\xAI - Medicine\microsoft-graph-to-do-api"
$batFile = "$workingDir\run_weekly.bat"

# Sunday 8:00 PM
$action = New-ScheduledTaskAction -Execute $batFile -WorkingDirectory $workingDir
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At '8:00PM'
Register-ScheduledTask -TaskName 'ToDoAI_WeeklySunday' -Action $action -Trigger $trigger -Description 'Weekly report on Sunday evening' -Force

# Wednesday 8:00 AM
$action = New-ScheduledTaskAction -Execute $batFile -WorkingDirectory $workingDir
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Wednesday -At '8:00AM'
Register-ScheduledTask -TaskName 'ToDoAI_WeeklyWednesday' -Action $action -Trigger $trigger -Description 'Weekly report on Wednesday morning' -Force

# Friday 5:00 PM
$action = New-ScheduledTaskAction -Execute $batFile -WorkingDirectory $workingDir
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Friday -At '5:00PM'
Register-ScheduledTask -TaskName 'ToDoAI_WeeklyFriday' -Action $action -Trigger $trigger -Description 'Weekly report on Friday evening' -Force

Write-Host "Weekly tasks created successfully!"
