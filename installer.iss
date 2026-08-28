; Inno-Setup-Skript für den Foto-Sortierer
; Kompilieren mit:  ISCC.exe installer.iss
; Ergebnis:         installer_output\Fotosortierer-Setup-1.0.0.exe

#define AppName "Foto-Sortierer"
#define AppVersion "1.0.0"
#define AppPublisher "Juergen Mutschall"
#define AppExeName "Fotosortierer.exe"

[Setup]
AppId={{8F3A6C21-4B7E-4E19-9C42-1D5A7E0B3F88}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\Fotosortierer
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=installer_output
OutputBaseFilename=Fotosortierer-Setup-{#AppVersion}
SetupIconFile=fotosortierer.ico
UninstallDisplayIcon={app}\{#AppExeName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
; "lowest" = Installation ohne Administratorrechte, kein UAC-Dialog für den Kunden
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "ANLEITUNG.md";       DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
Name: "{group}\{#AppName}";        Filename: "{app}\{#AppExeName}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}";  Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

; Hinweis: Einstellungen und Adressbuch liegen unter %APPDATA%\Fotosortierer
; und werden bei der Deinstallation absichtlich NICHT gelöscht.
