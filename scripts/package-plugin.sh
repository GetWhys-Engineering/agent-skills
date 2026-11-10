#!/usr/bin/env bash
#
# package-plugin.sh — build the Claude plugin.
#
# Builds dist/getwhys-skills/, a self-contained plugin folder:
#   .claude-plugin/plugin.json — the plugin manifest (version injected)
#   .claude-plugin/icon.png    — the directory listing icon
#   .mcp.json                  — credential-free remote MCP declaration
#   README.md                  — the directory listing's description
#   LICENSE
#   skills/<name>/             — every skill folder, copied verbatim
#
# The folder ships two ways:
#   - dist/getwhys-skills.zip, which the claude.ai org *Plugins* uploader (and
#     Claude Tag) expects: a zip rooted at .claude-plugin/plugin.json.
#   - the claude-directory branch, which Claude's plugin directory tracks
#     (scripts/publish-directory-branch.sh pushes this folder there).
# It is distinct from the per-skill *skill* zips (package-skills.sh) and the
# M365 Cowork package (package-cowork-plugin.sh). Skills load via the default
# skills/ scan, so plugin.json needs no skills array.
#
# Checks (the build fails on any of them):
#   - the folder follows the directory rules this build could break
#     (artifact-json.py verify-directory-plugin)
#   - Claude Code's validator with the directory profile, in strict mode
#     (claude plugin validate; run through npx, pinned). CI must run it; a
#     local run without npx or claude skips it with a warning.
#   - the zip holds the manifest and the MCP declaration (verify-claude-package)
#
# VERSION env var (a vX.Y.Z tag, leading v stripped) sets the manifest version;
# defaults to the version checked in to .claude-plugin/plugin.json.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_DIR="$REPO_ROOT/skills"
PLUGIN_MANIFEST="$REPO_ROOT/.claude-plugin/plugin.json"
MCP_CONFIG="$REPO_ROOT/packaging/claude-tag/.mcp.json"
DIRECTORY_FILES="$REPO_ROOT/packaging/claude-directory"
ARTIFACT_JSON="$REPO_ROOT/scripts/artifact-json.py"
DIST_DIR="$REPO_ROOT/dist"
PLUGIN_DIR="$DIST_DIR/getwhys-skills"
OUT_ZIP="$DIST_DIR/getwhys-skills.zip"
# Claude Code release whose `plugin validate --profile directory` CI runs.
CLAUDE_CODE_NPM="@anthropic-ai/claude-code@2.1.321"

VERSION="${VERSION:-}"
VERSION="${VERSION#v}"

for required in "$PLUGIN_MANIFEST" "$MCP_CONFIG" \
    "$DIRECTORY_FILES/README.md" "$DIRECTORY_FILES/icon.png" "$REPO_ROOT/LICENSE"; do
  if [ ! -f "$required" ]; then
    echo "FAIL: missing ${required#"$REPO_ROOT"/}" >&2
    exit 1
  fi
done

python3 "$ARTIFACT_JSON" validate-mcp "$MCP_CONFIG"

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

# --- stage the plugin folder ---
rm -rf "$PLUGIN_DIR" "$OUT_ZIP"
mkdir -p "$PLUGIN_DIR/.claude-plugin" "$PLUGIN_DIR/skills"

cp "$MCP_CONFIG" "$PLUGIN_DIR/.mcp.json"
cp "$DIRECTORY_FILES/icon.png" "$PLUGIN_DIR/.claude-plugin/icon.png"
cp "$DIRECTORY_FILES/README.md" "$PLUGIN_DIR/README.md"
cp "$REPO_ROOT/LICENSE" "$PLUGIN_DIR/LICENSE"

for name in $SKILL_NAMES; do
  cp -R "$SKILLS_DIR/$name" "$PLUGIN_DIR/skills/$name"
done

# --- render plugin.json (inject version; fail on invalid JSON or missing name) ---
python3 "$ARTIFACT_JSON" render-claude-manifest -- \
  "$PLUGIN_MANIFEST" "$PLUGIN_DIR/.claude-plugin/plugin.json" "$VERSION"
VERSION="$(python3 "$ARTIFACT_JSON" manifest-version "$PLUGIN_DIR/.claude-plugin/plugin.json")"

# --- check the folder against Claude's directory rules ---
python3 "$ARTIFACT_JSON" verify-directory-plugin "$PLUGIN_DIR"

if command -v npx >/dev/null 2>&1; then
  npx --yes "$CLAUDE_CODE_NPM" plugin validate --profile directory --strict "$PLUGIN_DIR"
elif command -v claude >/dev/null 2>&1; then
  claude plugin validate --profile directory --strict "$PLUGIN_DIR"
elif [ -n "${CI:-}" ]; then
  echo "FAIL: CI needs npx to run $CLAUDE_CODE_NPM plugin validate" >&2
  exit 1
else
  echo "WARNING: skipped claude plugin validate; install Node.js (npx) or Claude Code to run it." >&2
fi

# --- zip (.claude-plugin/ + .mcp.json + README + LICENSE + skills/ at the root) ---
(cd "$PLUGIN_DIR" && zip -r -X -q "$OUT_ZIP" . \
  -x '*.DS_Store' -x '*__MACOSX*')

python3 "$ARTIFACT_JSON" verify-claude-package "$OUT_ZIP"

echo "Built dist/getwhys-skills/ and dist/getwhys-skills.zip (version $VERSION, $SKILL_TOTAL skill(s))."
