#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

rm -rf "${root_dir}/artifacts/raw" "${root_dir}/artifacts/unknown"
mkdir -p "${root_dir}/artifacts"
