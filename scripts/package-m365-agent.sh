#!/usr/bin/env bash
# Build the provisioned GetWhys declarative-agent package for Microsoft 365.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE_DIR="$REPO_ROOT/packaging/m365-agent/appPackage"
ARTIFACT_JSON="$REPO_ROOT/scripts/artifact-json.py"
DIST_DIR="$REPO_ROOT/dist"
STAGE_DIR="$DIST_DIR/.m365-agent-stage"
OUT_ZIP="${OUTPUT_ZIP:-$DIST_DIR/getwhys-m365-agent.zip}"
CHECK_JSONSCHEMA="check-jsonschema==0.36.2"

APP_ID="${TEAMS_APP_ID:-}"
AUTH_ID="${GETWHYS_DCR_AUTH_ID:-}"
APP_NAME_SUFFIX="${APP_NAME_SUFFIX:-}"
VERSION="${VERSION:-${APP_VERSION:-}}"

if [ -z "$VERSION" ]; then
  VERSION="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' \
    "$REPO_ROOT/.claude-plugin/plugin.json")"
fi
VERSION="${VERSION#v}"

if [ -z "$APP_ID" ]; then
  echo "FAIL: TEAMS_APP_ID is empty; provision the Microsoft app before packaging." >&2
  exit 1
fi
if [ -z "$AUTH_ID" ]; then
  echo "FAIL: GETWHYS_DCR_AUTH_ID is empty; run the supported dcr/register provisioning workflow first." >&2
  exit 1
fi

rm -rf "$STAGE_DIR"
mkdir -p "$STAGE_DIR" "$(dirname "$OUT_ZIP")"

python3 "$ARTIFACT_JSON" render-m365-agent -- \
  "$SOURCE_DIR" "$STAGE_DIR" "$APP_ID" "$AUTH_ID" "$VERSION" "$APP_NAME_SUFFIX"
cp "$SOURCE_DIR/Color.png" "$SOURCE_DIR/Outline.png" "$STAGE_DIR/"

check_schema() {
  schema="$1"
  document="$2"
  if command -v uvx >/dev/null 2>&1; then
    uvx --quiet --from "$CHECK_JSONSCHEMA" check-jsonschema \
      --schemafile "$schema" "$document"
  elif command -v pipx >/dev/null 2>&1; then
    pipx run --spec "$CHECK_JSONSCHEMA" check-jsonschema \
      --schemafile "$schema" "$document"
  elif [ -n "${CI:-}" ]; then
    echo "FAIL: CI needs uvx or pipx for Microsoft schema validation." >&2
    exit 1
  else
    echo "WARNING: skipped schema validation for $document; install uv or pipx." >&2
  fi
}

check_schema \
  "https://developer.microsoft.com/json-schemas/teams/v1.30/MicrosoftTeams.schema.json" \
  "$STAGE_DIR/manifest.json"
check_schema \
  "https://developer.microsoft.com/json-schemas/copilot/declarative-agent/v1.9/schema.json" \
  "$STAGE_DIR/declarativeAgent.json"
check_schema \
  "https://developer.microsoft.com/json-schemas/copilot/plugin/v2.4/schema.json" \
  "$STAGE_DIR/ai-plugin.json"

rm -f "$OUT_ZIP"
(cd "$STAGE_DIR" && zip -r -X -q "$OUT_ZIP" . \
  -x '*.DS_Store' -x '*__MACOSX*' -x '.*' -x '*/.*')
rm -rf "$STAGE_DIR"

python3 "$ARTIFACT_JSON" verify-m365-agent-package "$OUT_ZIP"
echo "Built ${OUT_ZIP#$REPO_ROOT/} (version $VERSION)."
