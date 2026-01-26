# Troubleshooting

## `albion-dps` is not recognized
You need both:
1) an activated virtualenv
2) the project installed (so the console script exists)

Windows / PowerShell:
```
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -e ".[capture]"
albion-dps --help
```

Alternative (no install): run from the repo checkout
```
python -m albion_dps --help
python -m albion_dps live
```

## Live mode shows "no data"
Common causes:
- You are on the wrong interface: run `albion-dps live --list-interfaces` and pick the one that carries game traffic.
- No packets yet: start the game and generate traffic (zone change / combat).
- Capture dependencies missing: install `pcapy-ng` via `python -m pip install -e ".[capture]"`.
- Windows: Npcap not installed (or installed without WinPcap API compatibility).

## I see empty results while fighting
Strict "self + party only" filtering means the meter will not aggregate anything until it can resolve "self".
If you want deterministic startup, seed self:
```
albion-dps live --self-name "YourName"
```
or
```
albion-dps live --self-id 123456
```

## Too many "unknown payload" files
Unknown payloads are saved to `artifacts/unknown/` to support protocol updates.
Log lines for unknown payloads are printed only in `--debug`, but files are still written.

## Permission issues (Windows)
Npcap capture can require elevated permissions depending on configuration.
If capture fails, try running the terminal as Administrator and ensure Npcap is installed correctly.
