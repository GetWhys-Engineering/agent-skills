#!/usr/bin/env bash
# Build the portable OpenAI upload ZIP. VERSION optionally overrides plugin.json.
# RELEASE_NOTES optionally overrides the notes derived from git below.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
"$REPO_ROOT/scripts/validate-skills.sh"

# OpenAI reviews every uploaded package version and asks what changed. Default
# the manifest's release notes to the subjects of commits that touched packaged
# files since the previous v* tag.
if [ -z "${RELEASE_NOTES+set}" ]; then
  cd "$REPO_ROOT"
  if [ "$(git rev-parse --is-shallow-repository)" = "true" ]; then
    echo "FAIL: release notes need full git history (actions/checkout fetch-depth: 0)" >&2
    exit 1
  fi
  previous="$(git describe --tags --abbrev=0 --match 'v*' HEAD^ 2>/dev/null || true)"
  changes="$(git log --no-merges --format='- %s' ${previous:+"$previous.."}HEAD \
    -- skills plugin.json mcp.json assets LICENSE)"
  if [ -z "$changes" ]; then
    echo "Package content is unchanged since ${previous:-the first commit}; no OpenAI resubmission is needed."
    RELEASE_NOTES=""
  else
    RELEASE_NOTES="Changes since ${previous:-the first release}:
$changes"
  fi
  export RELEASE_NOTES
fi

python3 "$REPO_ROOT/scripts/package-openai-plugin.py"
