[Setup]
AppName=J-Filer
AppVersion=1.0.1
AppPublisher=Antigravity
DefaultDirName={autopf}\J-Filer
DisableProgramGroupPage=yes
OutputBaseFilename=J-Filer-Setup
Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\J-Filer.exe

[Files]
Source: "dist\J-Filer.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\J-Filer"; Filename: "{app}\J-Filer.exe"
Name: "{autodesktop}\J-Filer"; Filename: "{app}\J-Filer.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\J-Filer.exe"; Description: "Launch J-Filer"; Flags: nowait postinstall skipifsilent
