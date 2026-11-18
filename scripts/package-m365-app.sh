#!/usr/bin/env bash
#
# package-m365-app.sh — build the Microsoft 365 Marketplace app package.
#
# Produces dist/getwhys-m365.zip: the "GetWhys MCP" app on Microsoft
# Marketplace (WA200012755). Customers install it from the store; we upload
# this zip to Partner Center after each release. Contents, at the zip root:
#   manifest.json          — packaging/m365/manifest.json with the version set
#                            and one agentSkills entry per skills/<name>/ dir
#   Color.png, Outline.png — the listing's icons
#   skills/<name>/         — the same skill folders, copied verbatim
#
# The manifest keeps the live app's id and its agentConnectors entry, which
# names the public GetWhys MCP endpoint and a connection Microsoft stores, by
# ID only. scripts/artifact-json.py fails the build if credentials appear.
#
# Checks, each of which fails the build:
#   - the manifest's MCP connection carries no credentials (artifact-json.py)
#   - manifest.json validates against the schema its $schema names, which is
#     Microsoft's (check-jsonschema, run through uvx or pipx; needs network).
#     CI must run it; a local run without uvx or pipx skips it with a warning.
#   - the zip follows Microsoft's agentSkills package rules (artifact-json.py)
#
# VERSION (a vX.Y.Z tag) sets the app version to (X+1).Y.Z: Microsoft requires
# every upload to be higher than the last, and the app was published at 1.0.3
# before this script existed. Defaults to .claude-plugin/plugin.json's version.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_DIR="$REPO_ROOT/skills"
M365_DIR="$REPO_ROOT/packaging/m365"
ARTIFACT_JSON="$REPO_ROOT/scripts/artifact-json.py"
DIST_DIR="$REPO_ROOT/dist"
STAGE_DIR="$DIST_DIR/.m365-stage"
OUT_ZIP="$DIST_DIR/getwhys-m365.zip"
CHECK_JSONSCHEMA="check-jsonschema==0.38.2"

if [ -z "${VERSION:-}" ]; then
  VERSION="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' \
    "$REPO_ROOT/.claude-plugin/plugin.json")"
fi

# --- collect skill dirs ---
SKILL_NAMES=""
SKILL_TOTAL=0
for dir in "$SKILLS_DIR"/*/; do
  [ -d "$dir" ] || continue
  [ -f "$dir/SKILL.md" ] || continue
  SKILL_NAMES="$SKILL_NAMES $(basename "$dir")"
  SKILL_TOTAL=$((SKILL_TOTAL + 1))
done

if [ "$SKILL_TOTAL" -eq 0 ]; then
  echo "FAIL: no skills under skills/ to package." >&2
  exit 1
fi

# --- stage the package ---
rm -rf "$STAGE_DIR" "$OUT_ZIP"
mkdir -p "$STAGE_DIR/skills"

cp "$M365_DIR/Color.png" "$M365_DIR/Outline.png" "$STAGE_DIR/"
for name in $SKILL_NAMES; do
  cp -R "$SKILLS_DIR/$name" "$STAGE_DIR/skills/$name"
done

# --- render manifest.json (check credentials, set version, add agentSkills) ---
APP_VERSION="$(python3 "$ARTIFACT_JSON" render-m365-manifest -- \
  "$M365_DIR/manifest.json" "$STAGE_DIR/manifest.json" \
  "$VERSION" "$SKILL_NAMES")"

# --- check manifest.json against the schema it declares (Microsoft's) ---
SCHEMA_URL="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["$schema"])' \
  "$STAGE_DIR/manifest.json")"
if command -v uvx >/dev/null 2>&1; then
  uvx --quiet --from "$CHECK_JSONSCHEMA" check-jsonschema \
    --schemafile "$SCHEMA_URL" "$STAGE_DIR/manifest.json"
elif command -v pipx >/dev/null 2>&1; then
  pipx run --spec "$CHECK_JSONSCHEMA" check-jsonschema \
    --schemafile "$SCHEMA_URL" "$STAGE_DIR/manifest.json"
elif [ -n "${CI:-}" ]; then
  echo "FAIL: CI needs uvx or pipx to check manifest.json against $SCHEMA_URL" >&2
  exit 1
else
  echo "WARNING: skipped the manifest schema check; install uv or pipx to run it." >&2
fi

# --- zip (flat: manifest + icons + skills/ at the root; no hidden files) ---
(cd "$STAGE_DIR" && zip -r -X -q "$OUT_ZIP" . \
  -x '*.DS_Store' -x '*__MACOSX*' -x '.*' -x '*/.*')
rm -rf "$STAGE_DIR"

# --- check the zip against Microsoft's agentSkills package rules ---
python3 "$ARTIFACT_JSON" verify-m365-package "$OUT_ZIP"

echo "Built dist/getwhys-m365.zip (app version $APP_VERSION from $VERSION, $SKILL_TOTAL skill(s))."
