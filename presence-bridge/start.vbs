' Hidden launcher for SwitchBot presence bridge (no console window).
' Placed in Windows Startup folder by install.bat.
Dim fso, sh, dir
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")
dir = fso.GetParentFolderName(WScript.ScriptFullPath)
sh.Run Chr(34) & dir & "\venv\Scripts\pythonw.exe" & Chr(34) & _
       " " & Chr(34) & dir & "\bridge.py" & Chr(34), 0, False
