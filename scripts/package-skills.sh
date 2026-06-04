#!/usr/bin/env bash
#
# package-skills.sh — build one clean zip per skill into dist/.
#
# Each dist/<name>.zip contains the <name>/ folder at the zip root (the layout
# Claude.ai, ChatGPT, Amazon Q Business, and Perplexity uploads expect),
# with macOS cruft excluded. Used both locally (dry runs) and by CI on v* tags.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_DIR="$REPO_ROOT/skills"
DIST_DIR="$REPO_ROOT/dist"

mkdir -p "$DIST_DIR"

BUILT=0
for dir in "$SKILLS_DIR"/*/; do
  [ -d "$dir" ] || continue
  name="$(basename "$dir")"

  if [ ! -f "$dir/SKILL.md" ]; then
    echo "Skipping skills/$name (no SKILL.md)" >&2
    continue
  fi

  out="$DIST_DIR/$name.zip"
  rm -f "$out"
  # -X: no extra file attributes; run from skills/ so <name>/ sits at zip root.
  (cd "$SKILLS_DIR" && zip -r -X -q "$out" "$name" \
    -x '*.DS_Store' -x '*__MACOSX*')
  echo "Built dist/$name.zip"
  BUILT=$((BUILT + 1))
done

if [ "$BUILT" -eq 0 ]; then
  echo "No skills found under skills/ — nothing to package."
  exit 0
fi

echo "Packaged $BUILT skill(s) into dist/."
