Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "c:\Users\User\.gemini\antigravity\scratch\inventory-system"
WshShell.Run "py app.py", 0
Set WshShell = Nothing
