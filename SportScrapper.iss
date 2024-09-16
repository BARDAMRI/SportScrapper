[Setup]
AppName=SportScrapper
AppVersion=1.0
DefaultDirName={pf}\SportScrapper
DefaultGroupName=SportScrapper
OutputBaseFilename=SportScrapperSetup
DefaultDirFlags=uninsalwaysuninstall

[Files]
; Copy the executable
Source: "dist\SportScrapper.exe"; DestDir: "{app}"; Flags: ignoreversion

; Copy necessary assets
Source: "assets\config.json"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "assets\translations.json"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "assets\entrancePageImage.png"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "assets\icon.png"; DestDir: "{app}\assets"; Flags: ignoreversion

; Ensure the logs folder is created, but don't add files (empty folder)
Source: "logs\*"; DestDir: "{app}\logs"; Flags: createallsubdirs recursesubdirs

[Icons]
; Create a desktop icon
Name: "{group}\SportScrapper"; Filename: "{app}\SportScrapper.exe"; WorkingDir: "{app}"

[Run]
; Launch the program after installation
Filename: "{app}\SportScrapper.exe"; Description: "{cm:LaunchProgram, SportScrapper}"; Flags: nowait postinstall skipifsilent