#!/usr/bin/env python3
"""Render and validate JSON metadata used by packaged release artifacts."""

import argparse
import json
import sys
import zipfile


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


def verify_claude_package(args):
    try:
        with zipfile.ZipFile(args.archive) as archive:
            try:
                config = json.loads(archive.read(".mcp.json"))
            except KeyError:
                fail("packaged plugin is missing root-level .mcp.json")
            except json.JSONDecodeError as error:
                fail(f"packaged .mcp.json is invalid JSON: {error}")
    except (OSError, zipfile.BadZipFile) as error:
        fail(f"cannot read plugin archive {args.archive}: {error}")

    if config != EXPECTED_MCP_CONFIG:
        fail("packaged .mcp.json has an invalid GetWhys server declaration")


def render_cowork_manifest(args):
    manifest = read_json(args.source)
    manifest["version"] = args.version
    manifest["agentSkills"] = [
        {"folder": f"./skills/{name}"} for name in args.skill_names.split()
    ]
    write_json(args.output, manifest)


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

    return parser.parse_args()


def main():
    args = parse_args()
    args.run(args)


if __name__ == "__main__":
    main()
