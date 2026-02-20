# Windows Release Bootstrap Builder

Builds the canonical Windows release bootstrap executable:

- output name: `AlbionCommandDesk-Setup-vX.Y.Z-x86_64.exe`
- purpose: download tagged source zip, run `tools/install/windows/install.ps1`, and keep console open on error.

## Usage

From repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\release\windows\build_bootstrap_setup.ps1 -ReleaseTag v0.1.14
```

Custom output path:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\release\windows\build_bootstrap_setup.ps1 `
  -ReleaseTag v0.1.14 `
  -OutputPath .\dist\installer\AlbionCommandDesk-Setup-v0.1.14-x86_64.exe
```

## Notes

- `ReleaseTag` accepts tag (`vX.Y.Z`) or branch name.
- Bootstrap EXE installs into `%LOCALAPPDATA%\AlbionCommandDesk` (persistent path) instead of temp folders.
- Bootstrap EXE passes `-SkipCaptureExtras -SkipRun` to `install.ps1` for backward compatibility and to avoid failing startup on systems without Npcap.
- EXE requires outbound access to GitHub release/source URLs.
- Expected post-install paths:
  - runtime snapshot: `%LOCALAPPDATA%\AlbionCommandDesk\runtime\vX.Y.Z`
  - venv: `%LOCALAPPDATA%\AlbionCommandDesk\venv`
  - CLI: `%LOCALAPPDATA%\AlbionCommandDesk\venv\Scripts\albion-command-desk.exe`
- Expected launch commands:
  - `...\\albion-command-desk.exe core`
  - `...\\albion-command-desk.exe live` (requires Npcap Runtime)
- Bootstrap EXE also creates:
  - Desktop shortcut: `Albion Command Desk`
  - Start Menu shortcut folder: `Albion Command Desk`
