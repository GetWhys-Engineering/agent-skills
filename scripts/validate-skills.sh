#!/usr/bin/env bash
#
# validate-skills.sh — enforce skill hygiene for every skills/<name>/ directory.
#
# Checks (mirrors the limits enforced by the Claude.ai / ChatGPT upload UIs):
#   - each skills/<name>/ has a SKILL.md
#   - YAML frontmatter is present and first in the file
#   - `name`: <=64 chars, ^[a-z0-9-]+$, equals the directory name, no XML tags
#   - `description`: non-empty, <=1024 chars, no XML tags
#   - <200 files per skill directory
#   - no .DS_Store / __MACOSX / obvious secret patterns
#   - the Claude Tag package template is credential-free and no root .mcp.json exists
#
# Exits non-zero on any violation. Runs on macOS bash 3.2 and Linux.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_DIR="$REPO_ROOT/skills"
MCP_CONFIG="$REPO_ROOT/packaging/claude-tag/.mcp.json"
ROOT_MCP_CONFIG="$REPO_ROOT/.mcp.json"
ARTIFACT_JSON="$REPO_ROOT/scripts/artifact-json.py"

ERRORS=0

fail() {
  echo "FAIL: $1" >&2
  ERRORS=$((ERRORS + 1))
}

if [ ! -d "$SKILLS_DIR" ]; then
  echo "FAIL: skills/ directory not found at $SKILLS_DIR" >&2
  exit 1
fi

if [ -e "$ROOT_MCP_CONFIG" ]; then
  fail "root .mcp.json would be loaded by the Claude Code marketplace plugin"
fi

if [ ! -f "$MCP_CONFIG" ]; then
  fail "missing packaging/claude-tag/.mcp.json"
else
  if ! python3 "$ARTIFACT_JSON" validate-mcp "$MCP_CONFIG"; then
    fail "packaging/claude-tag/.mcp.json is invalid"
  fi
fi

# Extract a single-line frontmatter value for key $2 from SKILL.md $1.
# Only looks between the first pair of --- markers.
frontmatter_value() {
  awk -v key="$2" '
    NR == 1 && $0 == "---" { in_fm = 1; next }
    in_fm && $0 == "---"   { exit }
    in_fm && $0 ~ "^" key ":" {
      sub("^" key ":[ \t]*", "")
      # strip optional surrounding quotes
      gsub(/^["'"'"']|["'"'"']$/, "")
      print
      exit
    }
  ' "$1"
}

SKILL_COUNT=0

for dir in "$SKILLS_DIR"/*/; do
  [ -d "$dir" ] || continue
  SKILL_COUNT=$((SKILL_COUNT + 1))
  dirname_only="$(basename "$dir")"
  skill_md="$dir/SKILL.md"
  label="skills/$dirname_only"

  if [ ! -f "$skill_md" ]; then
    fail "$label: missing SKILL.md"
    continue
  fi

  # --- frontmatter must be first in the file ---
  if [ "$(head -n 1 "$skill_md")" != "---" ]; then
    fail "$label: SKILL.md must start with YAML frontmatter ('---' on line 1)"
    continue
  fi
  if ! awk 'NR > 1 && $0 == "---" { found = 1; exit } END { exit !found }' "$skill_md"; then
    fail "$label: frontmatter is not closed (no terminating '---')"
    continue
  fi

  name="$(frontmatter_value "$skill_md" "name")"
  description="$(frontmatter_value "$skill_md" "description")"

  # --- name ---
  if [ -z "$name" ]; then
    fail "$label: frontmatter is missing 'name'"
  else
    if [ "${#name}" -gt 64 ]; then
      fail "$label: name exceeds 64 characters (${#name})"
    fi
    if ! printf '%s' "$name" | grep -Eq '^[a-z0-9-]+$'; then
      fail "$label: name '$name' must match ^[a-z0-9-]+\$ (lowercase, numbers, hyphens)"
    fi
    if [ "$name" != "$dirname_only" ]; then
      fail "$label: name '$name' does not match directory name '$dirname_only'"
    fi
  fi

  # --- description ---
  if [ -z "$description" ]; then
    fail "$label: frontmatter is missing a non-empty single-line 'description'"
  else
    if [ "${#description}" -gt 1024 ]; then
      fail "$label: description exceeds 1024 characters (${#description})"
    fi
    case "$description" in
      *"<"*">"*) fail "$label: description must not contain XML/HTML tags" ;;
    esac
  fi
  case "$name" in
    *"<"*">"*) fail "$label: name must not contain XML/HTML tags" ;;
  esac

  # --- file count (<200 per skill, Claude upload limit) ---
  file_count="$(find "$dir" -type f | wc -l | tr -d ' ')"
  if [ "$file_count" -ge 200 ]; then
    fail "$label: contains $file_count files (must be fewer than 200)"
  fi

  # --- macOS cruft ---
  if find "$dir" \( -name '.DS_Store' -o -name '__MACOSX' \) | grep -q .; then
    fail "$label: contains .DS_Store or __MACOSX entries"
  fi

  # --- obvious secret patterns ---
  if grep -rEIl \
      -e 'AKIA[0-9A-Z]{16}' \
      -e '-----BEGIN [A-Z ]*PRIVATE KEY-----' \
      -e 'sk-[A-Za-z0-9_-]{20,}' \
      -e 'ghp_[A-Za-z0-9]{36}' \
      -e 'xox[baprs]-[A-Za-z0-9-]+' \
      "$dir" 2>/dev/null | grep -q .; then
    fail "$label: contains what looks like a secret (AWS key, private key, API token, ...)"
  fi
done

if [ "$SKILL_COUNT" -eq 0 ]; then
  echo "No skills found under skills/ — nothing to validate (OK)."
  exit 0
fi

if [ "$ERRORS" -gt 0 ]; then
  echo ""
  echo "Validation failed with $ERRORS error(s)." >&2
  exit 1
fi

echo "All $SKILL_COUNT skill(s) passed validation."
