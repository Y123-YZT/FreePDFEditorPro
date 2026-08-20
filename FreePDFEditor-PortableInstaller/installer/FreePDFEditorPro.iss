#define MyAppName "FreePDF Editor Pro"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "FreePDF Editor"
#define MyAppExeName "FreePDFEditorPro.exe"

[Setup]
AppId={{D2A1C7A8-4F7B-4D9E-9E4C-8F0A1C2B7A10}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\FreePDF Editor Pro
DefaultGroupName={#MyAppName}
OutputDir=output
OutputBaseFilename=FreePDFEditorPro-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}

[Files]
Source: "..\dist\FreePDFEditorPro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent
