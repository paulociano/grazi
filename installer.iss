; Inno Setup installer for Grazi.
#define AppName "Grazi"
#define AppVersion "0.9.0"
#define AppPublisher "Paulo Henrique Graciano"
#define AppExeName "Grazi.exe"

[Setup]
AppId={{A3F4D8CE-6EC4-4A41-9B6D-7E9C08F9F6A1}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\Grazi
DefaultGroupName=Grazi
OutputDir=installer-output
OutputBaseFilename=Grazi-Setup-v{#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#AppExeName}
DisableProgramGroupPage=yes

[Files]
Source: "dist\Grazi\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LEIA-ME.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "ABOUT.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autodesktop}\Grazi"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Grazi"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Documentação da Grazi"; Filename: "{app}\ABOUT.md"

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Iniciar a Grazi"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
