#!/usr/bin/env bash
# Validate the package source, exact ZIP layout, schemas, and public DCR metadata.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TEMP_DIR="$(mktemp -d)"
TEST_ZIP="$TEMP_DIR/getwhys-m365-agent.schema-test.zip"
HEADERS_FILE="$TEMP_DIR/mcp-headers"
BODY_FILE="$TEMP_DIR/mcp-body"

cleanup() {
  rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

TEAMS_APP_ID="171671ef-9243-419b-8408-4054cc5ec53f" \
GETWHYS_DCR_AUTH_ID="local-schema-validation-not-a-live-auth-config" \
APP_NAME_SUFFIX="-dev" \
VERSION="0.1.0" \
OUTPUT_ZIP="$TEST_ZIP" \
  "$REPO_ROOT/scripts/package-m365-agent.sh"

if command -v uvx >/dev/null 2>&1; then
  uvx --quiet --from check-jsonschema==0.36.2 check-jsonschema \
    --schemafile https://aka.ms/m365-agents-toolkits/v1.13/yaml.schema.json \
    "$REPO_ROOT/packaging/m365-agent/m365agents.yml"
elif command -v pipx >/dev/null 2>&1; then
  pipx run --spec check-jsonschema==0.36.2 check-jsonschema \
    --schemafile https://aka.ms/m365-agents-toolkits/v1.13/yaml.schema.json \
    "$REPO_ROOT/packaging/m365-agent/m365agents.yml"
elif [ -n "${CI:-}" ]; then
  echo "FAIL: CI needs uvx or pipx for Agents Toolkit lifecycle validation." >&2
  exit 1
else
  echo "WARNING: skipped Agents Toolkit lifecycle schema validation; install uv or pipx." >&2
fi

if [ "${SKIP_REMOTE_DCR_CHECK:-0}" = "1" ]; then
  echo "Skipped remote DCR metadata check."
  exit 0
fi

status="$(curl -sS --max-time 20 -D "$HEADERS_FILE" -o "$BODY_FILE" \
  -w '%{http_code}' https://api.getwhys.io/mcp/org)"
if [ "$status" != "401" ]; then
  echo "FAIL: unauthenticated MCP request returned HTTP $status, expected 401." >&2
  exit 1
fi
if ! tr -d '\r' < "$HEADERS_FILE" | grep -qi \
  'resource_metadata="https://api.getwhys.io/.well-known/oauth-protected-resource/mcp/org"'; then
  echo "FAIL: MCP 401 response does not advertise the expected protected-resource metadata." >&2
  exit 1
fi

protected_resource="$(curl -fsSL --max-time 20 \
  https://api.getwhys.io/.well-known/oauth-protected-resource/mcp/org)"
printf '%s' "$protected_resource" | jq -e '
  .resource == "https://api.getwhys.io/mcp/org" and
  (.authorization_servers | index("https://api.getwhys.io/mcp/org") != null) and
  (.scopes_supported | index("mcp:tools") != null)
' >/dev/null

authorization_server="$(curl -fsSL --max-time 20 \
  https://api.getwhys.io/.well-known/oauth-authorization-server/mcp/org)"
printf '%s' "$authorization_server" | jq -e '
  .issuer == "https://api.getwhys.io/mcp/org" and
  .registration_endpoint == "https://api.getwhys.io/mcp/org/oauth/register" and
  (.authorization_endpoint | type == "string") and
  (.token_endpoint | type == "string") and
  (.code_challenge_methods_supported | index("S256") != null) and
  (.grant_types_supported | index("authorization_code") != null) and
  (.token_endpoint_auth_methods_supported | index("none") != null) and
  (.token_endpoint_auth_methods_supported | index("client_secret_basic") != null) and
  (.token_endpoint_auth_methods_supported | index("client_secret_post") != null)
' >/dev/null

echo "Microsoft 365 declarative-agent source, package, and DCR metadata passed validation."
