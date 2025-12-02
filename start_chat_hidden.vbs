Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "c:\Users\bryan\OneDrive\Documents\xAI - Medicine\microsoft-graph-to-do-api"
' Use python (not pythonw) so you can see startup messages, but window minimizes after
WshShell.Run "cmd /c python chat_web.py", 7, False
