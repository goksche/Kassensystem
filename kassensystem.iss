[Setup]
AppName=Kassensystem
AppVersion=1.0
DefaultDirName={pf}\Kassensystem
DefaultGroupName=Kassensystem
OutputDir=.
OutputBaseFilename=KassensystemInstaller
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\run.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "config.py"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Kassensystem starten"; Filename: "{app}\run.exe"
Name: "{userdesktop}\Kassensystem"; Filename: "{app}\run.exe"; Tasks: desktopicon
Name: "{group}\Deinstallieren"; Filename: "{uninstallexe}"

[Tasks]
Name: "desktopicon"; Description: "Desktop-Verknüpfung erstellen"; GroupDescription: "Zusätzliche Aufgaben:"; Flags: unchecked

[Run]
Filename: "{app}\run.exe"; Description: "Kassensystem jetzt starten"; Flags: nowait postinstall skipifsilent
