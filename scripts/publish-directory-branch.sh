#!/usr/bin/env bash
#
# publish-directory-branch.sh — publish the built plugin to the branch that
# Claude's plugin directory tracks.
#
# The directory reads a plugin from a GitHub branch and scans the plugin folder.
# main's root can't be that folder: it also holds build scripts, CLAUDE.md, and
# other platforms' manifests, which the directory holds for review. So this
# script commits dist/getwhys-skills/ (built by package-plugin.sh) as the whole
# tree of the claude-directory branch, on top of the branch's previous commit.
#
# Never edit that branch by hand: the next publish replaces its contents.
# Change the skills, .claude-plugin/plugin.json, or packaging/claude-directory/
# on main instead.
#
# Runs from .github/workflows/claude-directory.yml, on every v* tag and on a
# manual run from main. DRY_RUN=1 builds the commit and lists it without
# pushing. DIRECTORY_BRANCH overrides the branch name.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN_DIR="$REPO_ROOT/dist/getwhys-skills"
ARTIFACT_JSON="$REPO_ROOT/scripts/artifact-json.py"
BRANCH="${DIRECTORY_BRANCH:-claude-directory}"
REMOTE="${REMOTE:-origin}"

if [ ! -f "$PLUGIN_DIR/.claude-plugin/plugin.json" ]; then
  echo "FAIL: no built plugin at dist/getwhys-skills/; run scripts/package-plugin.sh first" >&2
  exit 1
fi

VERSION="$(python3 "$ARTIFACT_JSON" manifest-version "$PLUGIN_DIR/.claude-plugin/plugin.json")"
SOURCE_SHA="$(git -C "$REPO_ROOT" rev-parse HEAD)"
SOURCE_REF="${GITHUB_REF_NAME:-$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD)}"
GIT_DIR_ABS="$(git -C "$REPO_ROOT" rev-parse --absolute-git-dir)"

# --- the branch's current commit, if the branch exists ---
PARENT=""
if git -C "$REPO_ROOT" ls-remote --exit-code --heads "$REMOTE" "$BRANCH" >/dev/null; then
  git -C "$REPO_ROOT" fetch --quiet --no-tags "$REMOTE" \
    "+refs/heads/$BRANCH:refs/remotes/$REMOTE/$BRANCH"
  PARENT="$(git -C "$REPO_ROOT" rev-parse "refs/remotes/$REMOTE/$BRANCH")"
fi

# --- write the plugin folder as a tree, through a throwaway index ---
INDEX="$(mktemp)"
rm -f "$INDEX"
trap 'rm -f "$INDEX"' EXIT

git_plugin() {
  (cd "$PLUGIN_DIR" && GIT_INDEX_FILE="$INDEX" \
    git --git-dir="$GIT_DIR_ABS" --work-tree=. "$@")
}
git_plugin add --all --force .
TREE="$(git_plugin write-tree)"

if [ -n "$PARENT" ] && [ "$(git -C "$REPO_ROOT" rev-parse "$PARENT^{tree}")" = "$TREE" ]; then
  echo "$BRANCH already holds this build (version $VERSION); nothing to publish."
  exit 0
fi

MESSAGE="getwhys-skills $VERSION

Built by scripts/publish-directory-branch.sh from $SOURCE_REF ($SOURCE_SHA).
Claude's plugin directory tracks this branch. Don't edit it by hand: the
next publish replaces its contents."

COMMIT="$(
  GIT_AUTHOR_NAME="${GIT_AUTHOR_NAME:-github-actions[bot]}" \
  GIT_AUTHOR_EMAIL="${GIT_AUTHOR_EMAIL:-41898282+github-actions[bot]@users.noreply.github.com}" \
  GIT_COMMITTER_NAME="${GIT_COMMITTER_NAME:-github-actions[bot]}" \
  GIT_COMMITTER_EMAIL="${GIT_COMMITTER_EMAIL:-41898282+github-actions[bot]@users.noreply.github.com}" \
  git -C "$REPO_ROOT" commit-tree "$TREE" ${PARENT:+-p "$PARENT"} -m "$MESSAGE"
)"

if [ "${DRY_RUN:-}" = "1" ]; then
  echo "DRY_RUN: would push $COMMIT to $BRANCH (parent: ${PARENT:-none, new branch}):"
  git -C "$REPO_ROOT" ls-tree -r --name-only "$COMMIT" | sed 's/^/  /'
  exit 0
fi

# A plain push: it fails rather than overwrite a commit another run pushed.
git -C "$REPO_ROOT" push --quiet "$REMOTE" "$COMMIT:refs/heads/$BRANCH"
echo "Published getwhys-skills $VERSION to $BRANCH ($COMMIT)."
