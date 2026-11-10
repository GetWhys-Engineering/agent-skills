#!/usr/bin/env python3
"""Render and validate JSON metadata used by packaged release artifacts."""

import argparse
import json
import re
import sys
import zipfile


PLUGIN_MANIFEST_MEMBER = ".claude-plugin/plugin.json"

# The Microsoft 365 Marketplace app's MCP connection may name only the public
# endpoint and a connection that Microsoft stores, never credentials.
M365_MCP_URL = "https://api.getwhys.io/mcp/org"
M365_SERVER_KEYS = {"mcpServerUrl", "authorization", "mcpToolDescription"}
M365_AUTH_KEYS = {"type", "referenceId"}

# Microsoft's package rules for agentSkills, from "Build plugins for Copilot
# Cowork" (learn.microsoft.com/microsoft-365/copilot/cowork/cowork-plugin-development).
M365_MAX_SKILLS = 20
M365_MAX_COMPANIONS = 20
M365_MAX_COMPANION_BYTES = 5 * 1024 * 1024
M365_MAX_COMPANION_TOTAL = 10 * 1024 * 1024
M365_SAFE_FILE_NAME = re.compile(r"[A-Za-z0-9._ !-]+")
M365_SKILL_NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
WINDOWS_RESERVED = re.compile(r"(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(\..*)?")

EXPECTED_MCP_CONFIG = {
    "mcpServers": {
        "getwhys": {
            "type": "http",
            "url": "https://api.getwhys.io/mcp/org",
        }
    }
}


def fail(message):
    sys.exit(f"FAIL: {message}")


def read_json(path):
    try:
        with open(path, encoding="utf-8") as source:
            return json.load(source)
    except (OSError, json.JSONDecodeError) as error:
        fail(f"cannot read JSON from {path}: {error}")


def write_json(path, value):
    try:
        with open(path, "w", encoding="utf-8") as destination:
            json.dump(value, destination, indent=2)
            destination.write("\n")
    except OSError as error:
        fail(f"cannot write JSON to {path}: {error}")


def validate_mcp(args):
    if read_json(args.config) != EXPECTED_MCP_CONFIG:
        fail(
            f"{args.config} must contain only the credential-free "
            "GetWhys HTTP server declaration"
        )


def render_claude_manifest(args):
    manifest = read_json(args.source)
    if not manifest.get("name"):
        fail("plugin.json has no 'name'")

    manifest["version"] = args.version
    write_json(args.output, manifest)


def read_member_json(archive, member):
    try:
        return json.loads(archive.read(member))
    except KeyError:
        fail(f"packaged plugin is missing {member}")
    except json.JSONDecodeError as error:
        fail(f"packaged {member} is invalid JSON: {error}")


def verify_claude_package(args):
    try:
        with zipfile.ZipFile(args.archive) as archive:
            config = read_member_json(archive, ".mcp.json")
            manifest = read_member_json(archive, PLUGIN_MANIFEST_MEMBER)
    except (OSError, zipfile.BadZipFile) as error:
        fail(f"cannot read plugin archive {args.archive}: {error}")

    if config != EXPECTED_MCP_CONFIG:
        fail("packaged .mcp.json has an invalid GetWhys server declaration")

    if not manifest.get("name"):
        fail(f"packaged {PLUGIN_MANIFEST_MEMBER} has no 'name'")


def render_cowork_manifest(args):
    manifest = read_json(args.source)
    manifest["version"] = args.version
    manifest["agentSkills"] = [
        {"folder": f"./skills/{name}"} for name in args.skill_names.split()
    ]
    write_json(args.output, manifest)


def check_m365_manifest(manifest, path):
    """Fail unless the source manifest is safe to publish and to build from."""
    if not manifest.get("id"):
        fail(f"{path} has no 'id'; it must keep the live app's id")
    if "agentSkills" in manifest:
        fail(f"{path} must not list agentSkills; the build adds one per skills/<name>/")

    connectors = manifest.get("agentConnectors") or []
    if not connectors:
        fail(f"{path} has no agentConnectors entry for the GetWhys MCP server")
    for connector in connectors:
        server = (connector.get("toolSource") or {}).get("remoteMcpServer")
        if not server:
            fail(f"{path}: connector {connector.get('id')!r} is not a remoteMcpServer")
        if server.get("mcpServerUrl") != M365_MCP_URL:
            fail(f"{path}: connector {connector.get('id')!r} must use {M365_MCP_URL}")
        extra = set(server) - M365_SERVER_KEYS
        if extra:
            fail(f"{path}: unexpected remoteMcpServer keys {sorted(extra)}")
        extra = set(server.get("authorization") or {}) - M365_AUTH_KEYS
        if extra:
            fail(
                f"{path}: authorization may hold only type and referenceId, "
                f"found {sorted(extra)}; credentials never go in this repo"
            )


def validate_m365_manifest(args):
    check_m365_manifest(read_json(args.manifest), args.manifest)


def m365_version(tag_version):
    """Map release tag vX.Y.Z to app version (X+1).Y.Z.

    Microsoft requires every upload to be higher than the last, and the app was
    published at 1.0.3 before this repo built it.
    """
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", tag_version)
    if not match:
        fail(f"version {tag_version!r} is not vX.Y.Z")
    major, minor, patch = (int(part) for part in match.groups())
    return f"{major + 1}.{minor}.{patch}"


def render_m365_manifest(args):
    manifest = read_json(args.source)
    check_m365_manifest(manifest, args.source)
    names = args.skill_names.split()
    if len(names) > M365_MAX_SKILLS:
        fail(f"{len(names)} skills exceed Microsoft's limit of {M365_MAX_SKILLS}")
    manifest["version"] = m365_version(args.version)
    manifest["agentSkills"] = [{"folder": f"./skills/{name}"} for name in names]
    write_json(args.output, manifest)
    print(manifest["version"])


def verify_m365_package(args):
    try:
        with zipfile.ZipFile(args.archive) as archive:
            members = {info.filename: info for info in archive.infolist()}
            manifest = read_member_json(archive, "manifest.json")
            skill_texts = {}
            for entry in manifest.get("agentSkills", []):
                folder = entry.get("folder", "").removeprefix("./").rstrip("/")
                member = f"{folder}/SKILL.md"
                if member not in members:
                    fail(f"agentSkills folder {folder!r} has no SKILL.md in the package")
                skill_texts[folder] = archive.read(member).decode("utf-8")
    except (OSError, zipfile.BadZipFile) as error:
        fail(f"cannot read package {args.archive}: {error}")

    check_m365_manifest(
        {key: value for key, value in manifest.items() if key != "agentSkills"},
        "packaged manifest.json",
    )
    for icon in (manifest.get("icons") or {}).values():
        if icon not in members:
            fail(f"icon {icon!r} named in manifest.json is missing from the package")

    for name in members:
        parts = name.rstrip("/").split("/")
        if any(part.startswith(".") or part == "__MACOSX" for part in parts):
            fail(f"hidden or macOS metadata entry {name!r} in the package")

    folders = [entry["folder"] for entry in manifest.get("agentSkills", [])]
    if len(folders) != len(set(folders)):
        fail("agentSkills lists a folder twice")

    for folder, text in skill_texts.items():
        frontmatter = re.match(r"---\n(.*?)\n---\n", text, re.S)
        if not frontmatter:
            fail(f"{folder}/SKILL.md has no YAML frontmatter")
        name = re.search(r"^name:\s*['\"]?([^'\"\s]+)", frontmatter.group(1), re.M)
        if not name or name.group(1) != folder.split("/")[-1]:
            fail(f"{folder}/SKILL.md 'name' must equal its folder name")
        if not M365_SKILL_NAME.fullmatch(name.group(1)):
            fail(f"{folder}/SKILL.md 'name' must be kebab-case")
        if not re.search(r"^description:\s*\S", frontmatter.group(1), re.M):
            fail(f"{folder}/SKILL.md has no description")

        companions = [
            info
            for member, info in members.items()
            if member.startswith(f"{folder}/")
            and not member.endswith("/")
            and member != f"{folder}/SKILL.md"
        ]
        if len(companions) > M365_MAX_COMPANIONS:
            fail(f"{folder} has {len(companions)} companion files (max {M365_MAX_COMPANIONS})")
        if sum(info.file_size for info in companions) > M365_MAX_COMPANION_TOTAL:
            fail(f"{folder} companion files exceed 10 MB in total")
        for info in companions:
            base = info.filename.split("/")[-1]
            if info.file_size > M365_MAX_COMPANION_BYTES:
                fail(f"{info.filename} is larger than 5 MB")
            if "\\" in info.filename or not M365_SAFE_FILE_NAME.fullmatch(base):
                fail(f"{info.filename} has characters Microsoft rejects")
            if WINDOWS_RESERVED.fullmatch(base):
                fail(f"{info.filename} uses a Windows reserved name")


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate-mcp")
    validate.add_argument("config")
    validate.set_defaults(run=validate_mcp)

    claude_manifest = commands.add_parser("render-claude-manifest")
    claude_manifest.add_argument("source")
    claude_manifest.add_argument("output")
    claude_manifest.add_argument("version")
    claude_manifest.set_defaults(run=render_claude_manifest)

    claude_package = commands.add_parser("verify-claude-package")
    claude_package.add_argument("archive")
    claude_package.set_defaults(run=verify_claude_package)

    cowork_manifest = commands.add_parser("render-cowork-manifest")
    cowork_manifest.add_argument("source")
    cowork_manifest.add_argument("output")
    cowork_manifest.add_argument("version")
    cowork_manifest.add_argument("skill_names")
    cowork_manifest.set_defaults(run=render_cowork_manifest)

    m365_validate = commands.add_parser("validate-m365-manifest")
    m365_validate.add_argument("manifest")
    m365_validate.set_defaults(run=validate_m365_manifest)

    m365_manifest = commands.add_parser("render-m365-manifest")
    m365_manifest.add_argument("source")
    m365_manifest.add_argument("output")
    m365_manifest.add_argument("version")
    m365_manifest.add_argument("skill_names")
    m365_manifest.set_defaults(run=render_m365_manifest)

    m365_package = commands.add_parser("verify-m365-package")
    m365_package.add_argument("archive")
    m365_package.set_defaults(run=verify_m365_package)

    return parser.parse_args()


def main():
    args = parse_args()
    args.run(args)


if __name__ == "__main__":
    main()
