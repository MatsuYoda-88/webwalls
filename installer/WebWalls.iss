; web.walls installer (Inno Setup 6)
; Build:  ISCC.exe /DAppVersion=0.6.0 installer\WebWalls.iss      (expects dist\WebWalls.exe to exist)
; Installs per-user (no admin prompt) to %LOCALAPPDATA%\Programs\web.walls

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

[Setup]
AppId={{3EE1E45E-8D99-467B-840B-5B6FCA3380B6}
AppName=web.walls
AppVersion={#AppVersion}
AppVerName=web.walls {#AppVersion}
AppPublisher=web.walls
AppComments=Animated HTML live wallpapers for your Windows desktop
DefaultDirName={autopf}\web.walls
DefaultGroupName=web.walls
DisableProgramGroupPage=yes
DisableDirPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.17763
OutputDir=..\release
OutputBaseFilename=WebWalls-Setup-{#AppVersion}
SetupIconFile=..\src\assets\webwalls.ico
UninstallDisplayIcon={app}\WebWalls.exe
UninstallDisplayName=web.walls
Compression=lzma2/normal
SolidCompression=yes
WizardStyle=modern
CloseApplications=no
RestartApplications=no

[Messages]
WelcomeLabel2=This will install web.walls {#AppVersion}: animated live wallpapers that run behind your desktop icons.%n%nIt works on every monitor (32:9 super-ultrawide, ultrawide and portrait too) and backs off automatically while you game.

[Tasks]
Name: "startup"; Description: "Start web.walls when I sign in to Windows"; GroupDescription: "Extras:"; Flags: unchecked
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Extras:"; Flags: unchecked

[Files]
Source: "..\dist\WebWalls.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Same name/place the app itself uses for its Start menu shortcut, so there's never a duplicate.
Name: "{userprograms}\WebWalls"; Filename: "{app}\WebWalls.exe"; WorkingDir: "{app}"; Comment: "web.walls: HTML live wallpapers for your desktop"
Name: "{userdesktop}\web.walls"; Filename: "{app}\WebWalls.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Registry]
; Same Run value the app's own "Start with Windows" toggle uses.
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "WebWalls"; ValueData: """{app}\WebWalls.exe"""; Tasks: startup; Flags: uninsdeletevalue

[Run]
Filename: "{app}\WebWalls.exe"; Description: "Start web.walls now"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Browser cache only. Settings and any wallpapers you added (in %APPDATA%\WebWalls) are kept.
Type: filesandordirs; Name: "{localappdata}\WebWalls"

[Code]
// Ask a running web.walls to close itself (so it restores the normal wallpaper), then make sure it's gone.
procedure CloseWebWalls(const ExePath: String);
var
  Code: Integer;
begin
  if FileExists(ExePath) then
  begin
    Exec(ExePath, '--quit', '', SW_HIDE, ewWaitUntilTerminated, Code);
    Sleep(1500);
  end;
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/im WebWalls.exe /f', '', SW_HIDE, ewWaitUntilTerminated, Code);
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  CloseWebWalls(ExpandConstant('{app}\WebWalls.exe'));
  Result := '';
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
    CloseWebWalls(ExpandConstant('{app}\WebWalls.exe'));
end;
