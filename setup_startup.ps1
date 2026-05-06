$WshShell = New-Object -comObject WScript.Shell
$StartupPath = [System.Environment]::GetFolderPath('Startup')
$Shortcut = $WshShell.CreateShortcut("$StartupPath\OmborxonaServer.lnk")
$Shortcut.TargetPath = "c:\Users\User\.gemini\antigravity\scratch\inventory-system\start_hidden.vbs"
$Shortcut.WorkingDirectory = "c:\Users\User\.gemini\antigravity\scratch\inventory-system"
$Shortcut.Save()
