pythonScriptPath = "C:\Absolute\Path\To\Miti-Tithi"
command = "cmd.exe /c cd /d """ & pythonScriptPath & """ && pythonw.exe """ & pythonScriptPath & "\main.py"""

Set WshShell = WScript.CreateObject("WScript.Shell")
WshShell.Run command, 0, False
Set WshShell = Nothing
