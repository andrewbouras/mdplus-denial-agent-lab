#!/bin/zsh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${1:-8766}"

cd "$ROOT/ui"
npm ci --silent
npm run build

cd "$ROOT"
exec "${PYTHON:-python3}" -m synthetic_harness.server --port "$PORT"
