# Windows Live Capture Audit

Date: 2026-04-01

Status: `PH11-CAP-110` in progress

## Goal

Explain why a clean Windows machine currently installs Albion Command Desk successfully but still falls back to `core` after the user installs only `Npcap Runtime`.

## Current end-user outcome

Observed on a clean Windows VM:

1. Bootstrap installer downloads source and installs Python automatically.
2. Windows installer starts with profile `capture`.
3. Installer detects:
   - missing `Npcap Runtime`
   - missing `Npcap SDK`
   - missing C/C++ build tools
4. Installer falls back to `core`.
5. User installs `Npcap Runtime` afterwards.
6. App detects runtime, but `live` still does not work because the Python capture backend was never built.

This leaves the user with:

- `core` mode working
- `live` mode unavailable
- a misleading recovery path that suggests reinstall/build steps not suitable for normal users

## Dependency split

### Runtime dependencies for Windows live capture

These must exist on the user machine at runtime:

- `Npcap Runtime`
- Python environment containing the capture backend importable as `pcapy`

### Build-time dependencies currently required by this project

These are only needed because the project currently tries to build the backend locally from source:

- `Npcap SDK` headers (`pcap.h`)
- Microsoft C/C++ build tools (`cl.exe`)
- a successful local wheel/source build of `pcapy-ng`

### Dependencies that are not normal user prerequisites

These should not be required for an end user who only wants `live`:

- `Npcap SDK`
- Visual C++ Build Tools
- manual `pip install -e ".[capture]"` recovery

## Current implementation map

### 1. Package metadata

File: `pyproject.toml`

- `capture = ["pcapy-ng>=1.0.0"]`
- default install profile is `capture`

Meaning:

- `live` depends on `pcapy-ng`
- there is no Windows-specific prebuilt delivery path yet
- installer currently relies on normal `pip install -e ".[capture]"` behavior

### 2. Installer behavior

File: `tools/install/windows/install.ps1`

Current flow:

1. profile defaults to `capture`
2. installer checks `Npcap Runtime`
3. installer checks `Npcap SDK`
4. if SDK is missing:
   - fallback to `core` unless `-StrictCapture`
5. install target becomes:
   - `.[capture]` for capture
   - `.` for core
6. if capture install fails:
   - fallback to `core`

Important consequence:

- Windows installer treats local SDK/build availability as a prerequisite for capture
- there is no mechanism to install a prebuilt Windows capture backend artifact

### 3. Runtime startup behavior

File: `albion_dps/capture/startup_policy.py`

Current Windows logic:

- runtime available + backend available -> `live`
- runtime missing -> fallback to `core`
- runtime available + backend missing -> fallback to `core`

Current message is technically true, but not product-correct:

- it tells the user to reinstall with capture profile
- that still implies a build path instead of a release-shipped component

### 4. Backend import behavior

File: `albion_dps/capture/live_capture.py`

Current logic:

- tries `import pcapy`
- if import fails, backend is considered missing

Meaning:

- any working Windows solution only needs to make `pcapy` importable at runtime
- the app does not care whether that came from:
  - local `pcapy-ng` source build
  - prebuilt wheel
  - another compatible package providing the same import surface

## Root cause

Windows `live` currently fails for normal users because:

1. the app uses a Python C-extension backend (`pcapy-ng`)
2. the installer only knows how to satisfy that dependency by building it locally
3. local build requires:
   - `Npcap SDK`
   - C/C++ build tools
4. clean Windows users do not have those tools

So the product problem is not `Npcap Runtime`.
The real blocker is **local build of the Python capture backend**.

## Chosen strategy

Recommended strategy: **prebuilt Windows capture backend artifact**

Why:

- smallest change to current code
- preserves `pcapy` import contract already used by `live_capture.py`
- removes `Npcap SDK` and compiler from end-user setup
- lets installer stay simple:
  - app install
  - install prebuilt backend
  - if runtime exists, `live` works

## Required implementation direction

### Must change

- Windows installer must prefer a bundled/prebuilt backend wheel over local source build.
- Runtime messaging must stop telling normal users to install SDK/build tools.
- Release process must publish the Windows capture backend artifact.

### Must remain true

- `Npcap Runtime` stays an end-user prerequisite for `live`
- `core` must remain a valid fallback when runtime is missing

## Immediate implementation work

Phase 11 starts with:

1. wiring installer support for a prebuilt Windows capture backend wheel
2. changing Windows capture fallback messages to match that delivery model
3. teaching release/readiness tooling to validate the wheel contract

