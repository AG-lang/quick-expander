Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

strScriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)
strPythonW = "pythonw.exe"

' Check if pythonw is in local AppData path
strLocalAppData = WshShell.ExpandEnvironmentStrings("%LOCALAPPDATA%")
strDefaultPyPath = strLocalAppData & "\Programs\Python\Python310\pythonw.exe"

If FSO.FileExists(strDefaultPyPath) Then
    strPythonW = strDefaultPyPath
End If

strMainPy = strScriptDir & "\main.py"
strCommand = """" & strPythonW & """ """ & strMainPy & """ --minimized"
WshShell.Run strCommand, 0, False
