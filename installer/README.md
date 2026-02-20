# Installer Notes (Current Model)

This project currently uses a bootstrap-first distribution model.

## Supported release assets

- Windows primary installer (bootstrap EXE):  
  `AlbionCommandDesk-Setup-vX.Y.Z-x86_64.exe`
- Linux bootstrap script:  
  `acd-install-linux-vX.Y.Z.sh`
- macOS bootstrap script:  
  `acd-install-macos-vX.Y.Z.sh`
- Release manifest:  
  `manifest.json`

Source of truth for naming and validation:
- `docs/release/RELEASE_CHECKLIST.md`
- `docs/release/RELEASE_MANIFEST_SPEC.md`

## Windows bootstrap behavior

The Windows release EXE:
1. Downloads tagged source zip from GitHub.
2. Extracts and copies runtime snapshot to:
   - `%LOCALAPPDATA%\AlbionCommandDesk\runtime\vX.Y.Z`
3. Creates/reuses virtual environment:
   - `%LOCALAPPDATA%\AlbionCommandDesk\venv`
4. Runs `tools/install/windows/install.ps1` with:
   - `-ProjectRoot <runtime-path>`
   - `-VenvPath <localappdata-venv>`
   - `-Profile core`
   - `-ReleaseVersion <X.Y.Z>`
   - `-SkipRun`
5. Creates Desktop + Start Menu shortcuts targeting `core` mode.
6. Prints launch commands at the end.

## Launch commands after Windows EXE install

```powershell
& "$env:LOCALAPPDATA\AlbionCommandDesk\venv\Scripts\albion-command-desk.exe" core
# live capture (Npcap Runtime required):
# & "$env:LOCALAPPDATA\AlbionCommandDesk\venv\Scripts\albion-command-desk.exe" live
```

## Legacy packaging status

Legacy NSIS/DEB/RPM/DMG packaging docs were removed from this file because they do not match the current release pipeline.

Current release process:
- build/bootstrap instructions: `tools/release/windows/README.md`
- release runbook: `docs/release/RELEASE_RUNBOOK.md`
