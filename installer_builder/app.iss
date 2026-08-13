#define MyAppName "AI Summarizer"
#define MyAppVersion GetEnv("VERSION")
#define MyAppExeName "ai-summarizer.exe"
#define MyAppDistDir "..\dist\ai-summarizer"

[Setup]
AppId=ru.vdm17.aisummarizer
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=vdm17
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
PrivilegesRequired=admin
ChangesEnvironment=yes

OutputDir=..\dist\
OutputBaseFilename=AISummarizer-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes

[Files]
Source: "{#MyAppDistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Code]
const
  EnvironmentKey =
    'SYSTEM\CurrentControlSet\Control\Session Manager\Environment';
  StateKey = 'Software\vdm17\ai-summarizer';

function NormalizePathEntry(const Value: String): String;
begin
  Result := RemoveBackslashUnlessRoot(Trim(Value));
end;

function PathContains(const PathValue, Directory: String): Boolean;
var
  Entries: TArrayOfString;
  I: Integer;
begin
  Result := False;
  Entries := StringSplit(PathValue, [';'], stAll);

  for I := 0 to GetArrayLength(Entries) - 1 do
  begin
    if CompareText(NormalizePathEntry(Entries[I]),
      NormalizePathEntry(Directory)) = 0 then
    begin
      Result := True;
      Exit;
    end;
  end;
end;

function AddToSystemPath(const Directory: String; var Added: Boolean): Boolean;
var
  PathValue: String;
begin
  Added := False;

  if not RegQueryStringValue(HKEY_LOCAL_MACHINE, EnvironmentKey, 'Path',
    PathValue) then
    PathValue := '';

  if PathContains(PathValue, Directory) then
  begin
    Result := True;
    Exit;
  end;

  if (PathValue <> '') and (PathValue[Length(PathValue)] <> ';') then
    PathValue := PathValue + ';';

  Result := RegWriteExpandStringValue(
    HKEY_LOCAL_MACHINE, EnvironmentKey, 'Path', PathValue + Directory);

  Added := Result;
end;

function RemoveFromSystemPath(const Directory: String): Boolean;
var
  PathValue, NewPath: String;
  Entries: TArrayOfString;
  I, IndexToRemove: Integer;
begin
  Result := True;

  if not RegQueryStringValue(HKEY_LOCAL_MACHINE, EnvironmentKey, 'Path',
    PathValue) then
    Exit;

  Entries := StringSplit(PathValue, [';'], stAll);
  IndexToRemove := -1;

  for I := 0 to GetArrayLength(Entries) - 1 do
    if CompareText(NormalizePathEntry(Entries[I]),
      NormalizePathEntry(Directory)) = 0 then
      IndexToRemove := I;

  if IndexToRemove = -1 then
    Exit;

  NewPath := '';
  for I := 0 to GetArrayLength(Entries) - 1 do
    if I <> IndexToRemove then
    begin
      if NewPath <> '' then
        NewPath := NewPath + ';';
      NewPath := NewPath + Entries[I];
    end;

  Result := RegWriteExpandStringValue(
    HKEY_LOCAL_MACHINE, EnvironmentKey, 'Path', NewPath);
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  AppDir: String;
  Added: Boolean;
begin
  if CurStep = ssPostInstall then
  begin
    AppDir := ExpandConstant('{app}');

    if AddToSystemPath(AppDir, Added) then
    begin
      if Added then
        RegWriteStringValue(
          HKEY_LOCAL_MACHINE, StateKey, 'PathEntry', AppDir);
    end
    else
      MsgBox(
        'Unable to add program directory to PATH.',
        mbError, MB_OK);
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  AppDir: String;
begin
  if CurUninstallStep = usUninstall then
    if RegQueryStringValue(HKEY_LOCAL_MACHINE, StateKey, 'PathEntry',
      AppDir) then
      if RemoveFromSystemPath(AppDir) then
      begin
        RegDeleteValue(HKEY_LOCAL_MACHINE, StateKey, 'PathEntry');
        RegDeleteKeyIfEmpty(HKEY_LOCAL_MACHINE, StateKey);
      end;
end;
