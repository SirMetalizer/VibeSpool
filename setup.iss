; Inno Setup Script for VibeSpool
; Generated automatically by generate_setup.py

[Setup]
AppName=VibeSpool
AppVersion=2.2.2
DefaultDirName={autopf}\VibeSpool
DefaultGroupName=VibeSpool
OutputDir=dist
OutputBaseFilename=VibeSpool_Setup
SetupIconFile=core\vibespool-icon.ico
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest

[Files]
Source: "dist\VibeSpool_Win.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\VibeSpool"; Filename: "{app}\VibeSpool_Win.exe"
Name: "{autodesktop}\VibeSpool"; Filename: "{app}\VibeSpool_Win.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Desktop-Symbol erstellen"; GroupDescription: "Zusatzliche Symbole:"
