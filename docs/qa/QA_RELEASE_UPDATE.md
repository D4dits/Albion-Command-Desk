# QA-003 Release + Manifest + Update Banner Validation

Goal: verify end-to-end update signaling between release metadata and in-app banner.

## 1) Validate manifest contract + update checker behavior (local)

Run tests:
```
.\venv\Scripts\python -m pytest -q tests/test_update_checker.py tests/test_release_manifest_contract.py tests/test_qt_update_banner.py
```

## 2) Validate banner flow against a manifest payload (local smoke)

```
.\venv\Scripts\python .\tools\qa\verify_release_update_flow.py
```

Expected output:
- `PASS: release manifest + update banner flow validated`

## 3) Validate release workflow output (GitHub)

After publishing release/tag:
1. Run or verify `.github/workflows/release-manifest.yml`.
2. Confirm `manifest.json` is attached to the release.
3. Confirm app header shows:
   - `Update available: <current> -> <latest>`
   - working `Open` button to release URL.
