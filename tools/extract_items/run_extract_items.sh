#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  run_extract_items.sh --game-root <path> [--output <path>] [--server live|staging|playground]

Example:
  ./tools/extract_items/run_extract_items.sh --game-root "/opt/albion-online"
EOF
}

GAME_ROOT=""
OUTPUT_DIR=""
SERVER="live"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --game-root|-g)
      GAME_ROOT="${2:-}"
      shift 2
      ;;
    --output|-o)
      OUTPUT_DIR="${2:-}"
      shift 2
      ;;
    --server|-s)
      SERVER="${2:-}"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1"
      usage
      exit 1
      ;;
  esac
done

if [[ -z "$GAME_ROOT" ]]; then
  usage
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TOOL_PROJECT="$REPO_ROOT/tools/extract_items/ExtractItems.csproj"

if [[ -z "$OUTPUT_DIR" ]]; then
  OUTPUT_DIR="$REPO_ROOT/data"
fi

if [[ -z "${DOTNET_CLI_HOME:-}" ]]; then
  export DOTNET_CLI_HOME="$REPO_ROOT/artifacts/dotnet"
fi
export DOTNET_CLI_UI_LANGUAGE="en"
export DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1
if [[ -z "${NUGET_PACKAGES:-}" ]]; then
  export NUGET_PACKAGES="$REPO_ROOT/artifacts/nuget"
fi

DOTNET_BIN="dotnet"
if [[ -n "${DOTNET_ROOT:-}" && -x "${DOTNET_ROOT}/dotnet" ]]; then
  DOTNET_BIN="${DOTNET_ROOT}/dotnet"
elif [[ -x "${HOME}/.dotnet/dotnet" ]]; then
  DOTNET_BIN="${HOME}/.dotnet/dotnet"
fi

BUILD_PROPS=()
OBJ_DIR="$REPO_ROOT/tools/extract_items/obj"
if [[ ! -w "$OBJ_DIR" ]]; then
  INTERMEDIATE_ROOT="${EXTRACT_ITEMS_INTERMEDIATE:-/tmp/extract_items_obj}"
  OUTPUT_ROOT="${EXTRACT_ITEMS_OUTPUT:-/tmp/extract_items_bin}"
  mkdir -p "$INTERMEDIATE_ROOT" "$OUTPUT_ROOT"
  BUILD_PROPS+=("-p:BaseIntermediateOutputPath=$INTERMEDIATE_ROOT/")
  BUILD_PROPS+=("-p:IntermediateOutputPath=$INTERMEDIATE_ROOT/")
  BUILD_PROPS+=("-p:BaseOutputPath=$OUTPUT_ROOT/")
fi

"$DOTNET_BIN" build "$TOOL_PROJECT" -c Release "${BUILD_PROPS[@]}"
"$DOTNET_BIN" run --project "$TOOL_PROJECT" -c Release --no-build "${BUILD_PROPS[@]}" -- --game-root "$GAME_ROOT" --output "$OUTPUT_DIR" --server "$SERVER"
