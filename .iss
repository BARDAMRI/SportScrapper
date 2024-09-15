[Setup]
AppName=SportScrapper
AppVersion=1.0
DefaultDirName={pf}\SportScrapper
DefaultGroupName=SportScrapper

[Files]
Source: "dist\SportScrapper.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs
Source: "logs\*"; DestDir: "{app}\logs"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\SportScrapper"; Filename: "{app}\SportScrapper.exe"

[Run]
Filename: "{app}\SportScrapper.exe"; Description: "{cm:LaunchProgram, SportScrapper}"