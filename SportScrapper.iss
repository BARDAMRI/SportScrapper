[Setup]
AppName=SportScrapper
AppVersion=1.0
DefaultDirName={pf}\SportScrapper
DefaultGroupName=SportScrapper
OutputBaseFilename=SportScrapperSetup

[Files]
Source: "dist\SportScrapper.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "assets\config.json"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "assets\translations.json"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "assets\entrancePageImage.png"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "assets\icon.png"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "logs\*"; DestDir: "{app}\logs"; Flags: createallsubdirs
; Note: An empty logs folder will be created, but no files are copied inside it.

[Icons]
Name: "{group}\SportScrapper"; Filename: "{app}\SportScrapper.exe"

[Run]
Filename: "{app}\SportScrapper.exe"; Description: "{cm:LaunchProgram, SportScrapper}"