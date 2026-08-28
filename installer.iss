; Inno-Setup-Skript fuer den Foto-Sortierer
;
; Erzeugt einen Setup-Assistenten mit Lizenzseite, Fortschrittsanzeige,
; Startmenue-Eintrag und Deinstallation ueber "Apps & Features".
;
; Kompilieren:  ISCC.exe installer.iss   (uebernimmt build.ps1)
; Ergebnis:     dist\Fotosortierer-Setup-<version>.exe

#define AppName "Foto-Sortierer"
; Die Version reicht build.ps1 aus pfade.py herein, damit sie nicht
; an zwei Stellen gepflegt werden muss.
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#define AppPublisher "Juergen Mutscheller - mutschweb"
#define AppExeName "Fotosortierer.exe"

[Setup]
AppId={{8F3A6C21-4B7E-4E19-9C42-1D5A7E0B3F88}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\Fotosortierer
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=dist
OutputBaseFilename=Fotosortierer-Setup-{#AppVersion}
SetupIconFile=fotosortierer.ico
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
; Die GPL verlangt, dass der Empfaenger die Lizenz zu sehen bekommt.
LicenseFile=LICENSE
; "lowest": Installation ohne Administratorrechte, kein UAC-Dialog beim Kunden.
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Der komplette Programmordner samt Bibliotheken und eingebettetem Quellcode.
; Nuitka legt alles flach in den Ordner, es gibt kein _internal.
Source: "dist\Fotosortierer\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

; Hinweis: Einstellungen und Adressbuch liegen unter %APPDATA%\Fotosortierer
; und werden bei der Deinstallation absichtlich NICHT geloescht.
