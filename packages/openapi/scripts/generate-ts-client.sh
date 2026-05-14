#!/usr/bin/env bash
# Regenerate apps/web/src/lib/api/generated/schema.ts from the OpenAPI export.
# Run via `make openapi` after `apps/api/scripts/export_openapi.py`.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
SCHEMA="$REPO_ROOT/packages/openapi/openapi.json"
OUTPUT="$REPO_ROOT/apps/web/src/lib/api/generated/schema.ts"
LOCAL_BIN="$REPO_ROOT/apps/web/node_modules/.bin/openapi-typescript"

if [[ ! -f "$SCHEMA" ]]; then
  echo "ERROR: $SCHEMA not found. Run 'uv run python scripts/export_openapi.py' first." >&2
  exit 1
fi

if [[ ! -x "$LOCAL_BIN" ]]; then
  echo "ERROR: $LOCAL_BIN not found. Run 'npm ci --legacy-peer-deps' inside apps/web." >&2
  exit 1
fi

mkdir -p "$(dirname "$OUTPUT")"

"$LOCAL_BIN" "$SCHEMA" -o "$OUTPUT"

echo "TS schema written to ${OUTPUT#"$REPO_ROOT/"}"
