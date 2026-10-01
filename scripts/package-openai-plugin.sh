#!/usr/bin/env bash
# Build the portable OpenAI upload ZIP. VERSION optionally overrides plugin.json.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
"$REPO_ROOT/scripts/validate-skills.sh"
python3 "$REPO_ROOT/scripts/package-openai-plugin.py"
