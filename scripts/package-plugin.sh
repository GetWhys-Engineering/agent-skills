#!/usr/bin/env bash
#
# package-plugin.sh — build the Claude Tag plugin package.
#
# Produces dist/getwhys-skills.zip, a self-contained plugin:
#   .claude-plugin/plugin.json — the plugin manifest (version injected)
#   .mcp.json                  — credential-free remote MCP declaration
#   skills/<name>/             — every skill folder, copied verbatim
#
# This is the artifact the claude.ai org *Plugins* uploader (and Claude Tag)
# expects: a zip rooted at .claude-plugin/plugin.json. It is distinct from the
# per-skill *skill* zips (package-skills.sh) and the M365 Cowork package
# (package-cowork-plugin.sh). Skills load via the default skills/ scan, so
# plugin.json needs no skills array.
#
# VERSION env var (or a vX.Y.Z git tag stripped of the leading v) sets the
# manifest version; defaults to 0.1.0.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_DIR="$REPO_ROOT/skills"
PLUGIN_MANIFEST="$REPO_ROOT/.claude-plugin/plugin.json"
MCP_CONFIG="$REPO_ROOT/packaging/claude-tag/.mcp.json"
DIST_DIR="$REPO_ROOT/dist"
STAGE_DIR="$DIST_DIR/.plugin-stage"
OUT_ZIP="$DIST_DIR/getwhys-skills.zip"

VERSION="${VERSION:-0.1.0}"
VERSION="${VERSION#v}"

if [ ! -f "$PLUGIN_MANIFEST" ]; then
  echo "FAIL: missing .claude-plugin/plugin.json" >&2
  exit 1
fi

if [ ! -f "$MCP_CONFIG" ]; then
  echo "FAIL: missing packaging/claude-tag/.mcp.json" >&2
  exit 1
fi

python3 - "$MCP_CONFIG" <<'PY'
import json, sys

with open(sys.argv[1]) as f:
    config = json.load(f)

expected = {
    "mcpServers": {
        "getwhys": {
            "type": "http",
            "url": "https://api.getwhys.io/mcp/org",
        }
    }
}
if config != expected:
    sys.exit("FAIL: packaging/claude-tag/.mcp.json must contain only the credential-free GetWhys HTTP server declaration")
PY

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
  echo "No skills found under skills/ — skipping plugin build."
  exit 0
fi

# --- stage the package ---
rm -rf "$STAGE_DIR" "$OUT_ZIP"
mkdir -p "$STAGE_DIR/.claude-plugin" "$STAGE_DIR/skills"

cp "$MCP_CONFIG" "$STAGE_DIR/.mcp.json"

for name in $SKILL_NAMES; do
  cp -R "$SKILLS_DIR/$name" "$STAGE_DIR/skills/$name"
done

# --- render plugin.json (inject version; fail on invalid JSON or missing name) ---
VERSION="$VERSION" python3 - "$PLUGIN_MANIFEST" "$STAGE_DIR/.claude-plugin/plugin.json" <<'PY'
import json, os, sys

src, out = sys.argv[1], sys.argv[2]
with open(src) as f:
    manifest = json.load(f)

if not manifest.get("name"):
    sys.exit("FAIL: plugin.json has no 'name'")

manifest["version"] = os.environ["VERSION"]

with open(out, "w") as f:
    json.dump(manifest, f, indent=2)
    f.write("\n")
PY

# --- zip (.claude-plugin/ + .mcp.json + skills/ at the package root) ---
(cd "$STAGE_DIR" && zip -r -X -q "$OUT_ZIP" . \
  -x '*.DS_Store' -x '*__MACOSX*')
rm -rf "$STAGE_DIR"

python3 - "$OUT_ZIP" <<'PY'
import json, sys, zipfile

with zipfile.ZipFile(sys.argv[1]) as archive:
    if ".mcp.json" not in archive.namelist():
        sys.exit("FAIL: packaged plugin is missing root-level .mcp.json")
    config = json.loads(archive.read(".mcp.json"))

expected = {
    "mcpServers": {
        "getwhys": {
            "type": "http",
            "url": "https://api.getwhys.io/mcp/org",
        }
    }
}
if config != expected:
    sys.exit("FAIL: packaged .mcp.json has an invalid GetWhys server declaration")
PY

echo "Built dist/getwhys-skills.zip (version $VERSION, $SKILL_TOTAL skill(s))."
