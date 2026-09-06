[Setup]
AppName=TONI
AppVersion=3.5
AppPublisher=Frahn
DefaultDirName={localappdata}\TONI
DefaultGroupName=TONI
OutputBaseFilename=TONI-Setup
SetupIconFile=toni.ico
LicenseFile=licencia.txt
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
UninstallDisplayName=TONI - Asistente de Voz
CloseApplications=yes

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "startup"; Description: "Iniciar TONI automáticamente al prender la PC"

[Files]
Source: "dist\TONI\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\TONI"; Filename: "{app}\TONI.exe"
Name: "{autodesktop}\TONI"; Filename: "{app}\TONI.exe"

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "TONI"; ValueData: """{app}\TONI.exe"""; Flags: uninsdeletevalue; Tasks: startup

[Run]
Filename: "{app}\TONI.exe"; Description: "Abrir TONI ahora"; Flags: nowait postinstall