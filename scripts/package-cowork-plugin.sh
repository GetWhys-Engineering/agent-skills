#!/usr/bin/env bash
#
# package-cowork-plugin.sh — build the Microsoft 365 Copilot Cowork org plugin.
#
# Produces dist/getwhys-cowork.zip (M365 Unified App Manifest v1.28 package):
#   manifest.json   — from cowork/manifest.template.json, with one
#                     agentSkills entry per skills/<name>/ dir injected
#   color.png       — 192x192 GetWhys icon
#   outline.png     — 32x32 outline icon
#   skills/<name>/  — the same skill folders, copied verbatim
#
# Skills-only package: no agentConnectors / MCP config ever ships from here.
# VERSION env var (or a vX.Y.Z git tag stripped of the leading v) sets the
# manifest version; defaults to 0.1.0.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_DIR="$REPO_ROOT/skills"
COWORK_DIR="$REPO_ROOT/cowork"
DIST_DIR="$REPO_ROOT/dist"
STAGE_DIR="$DIST_DIR/.cowork-stage"
OUT_ZIP="$DIST_DIR/getwhys-cowork.zip"

VERSION="${VERSION:-0.1.0}"
VERSION="${VERSION#v}"

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
  echo "No skills found under skills/ — skipping Cowork plugin build."
  exit 0
fi

# Microsoft caps agentSkills at 20 entries per package.
if [ "$SKILL_TOTAL" -gt 20 ]; then
  echo "FAIL: $SKILL_TOTAL skills exceed the M365 limit of 20 agentSkills per package." >&2
  exit 1
fi

# --- stage the package ---
rm -rf "$STAGE_DIR" "$OUT_ZIP"
mkdir -p "$STAGE_DIR/skills"

cp "$COWORK_DIR/color.png" "$COWORK_DIR/outline.png" "$STAGE_DIR/"
for name in $SKILL_NAMES; do
  cp -R "$SKILLS_DIR/$name" "$STAGE_DIR/skills/$name"
done

# --- render manifest.json (inject version + agentSkills array) ---
SKILL_NAMES="$SKILL_NAMES" VERSION="$VERSION" python3 - "$COWORK_DIR/manifest.template.json" "$STAGE_DIR/manifest.json" <<'PY'
import json, os, sys

template_path, out_path = sys.argv[1], sys.argv[2]
with open(template_path) as f:
    manifest = json.load(f)

manifest["version"] = os.environ["VERSION"]
manifest["agentSkills"] = [
    {"folder": f"./skills/{name}"} for name in os.environ["SKILL_NAMES"].split()
]

with open(out_path, "w") as f:
    json.dump(manifest, f, indent=2)
    f.write("\n")
PY

# --- zip (flat: manifest + icons + skills/ at the package root) ---
(cd "$STAGE_DIR" && zip -r -X -q "$OUT_ZIP" . \
  -x '*.DS_Store' -x '*__MACOSX*')
rm -rf "$STAGE_DIR"

echo "Built dist/getwhys-cowork.zip (version $VERSION, $SKILL_TOTAL skill(s))."
