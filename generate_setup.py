import re

def main():
    # Read version from core/constants.py
    with open("core/constants.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    version_match = re.search(r'APP_VERSION\s*=\s*"([^"]+)"', content)
    if not version_match:
        raise ValueError("Could not find APP_VERSION in core/constants.py")
    
    version = version_match.group(1)
    print(f"Generating setup.iss for VibeSpool version {version}...")
    
    iss_content = f"""; Inno Setup Script for VibeSpool
; Generated automatically by generate_setup.py

[Setup]
AppName=VibeSpool
AppVersion={version}
DefaultDirName={{autopf}}\\VibeSpool
DefaultGroupName=VibeSpool
OutputDir=dist
OutputBaseFilename=VibeSpool_Setup
SetupIconFile=core\\vibespool-icon.ico
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest

[Files]
Source: "dist\\VibeSpool_Win.exe"; DestDir: "{{app}}"; Flags: ignoreversion

[Icons]
Name: "{{group}}\\VibeSpool"; Filename: "{{app}}\\VibeSpool_Win.exe"
Name: "{{autodesktop}}\\VibeSpool"; Filename: "{{app}}\\VibeSpool_Win.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Desktop-Symbol erstellen"; GroupDescription: "Zusatzliche Symbole:"
"""

    with open("setup.iss", "w", encoding="utf-8") as f:
        f.write(iss_content)
    print("setup.iss generated successfully.")

if __name__ == "__main__":
    main()
