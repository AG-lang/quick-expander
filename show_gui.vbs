Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
strScriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)
strCommand = "pythonw.exe """ & strScriptDir & "\main.py"""
WshShell.Run strCommand, 0, False
