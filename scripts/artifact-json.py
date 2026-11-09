#!/usr/bin/env python3
"""Render and validate JSON metadata used by packaged release artifacts."""

import argparse
import json
import re
import struct
import sys
import zipfile
from pathlib import Path


PLUGIN_MANIFEST_MEMBER = ".claude-plugin/plugin.json"

# Claude's plugin directory rules that this build could break. Sources:
# https://claude.com/docs/plugins/pre-submission-checklist and the portal's
# validation report. Anything outside these holds the version for a reviewer,
# blocks it, or is refused from organizations Anthropic hasn't Verified.
DIRECTORY_REQUIRED_KEYS = ("name", "version", "description", "author", "privacyPolicyUrl")
DIRECTORY_TEXT_SUFFIXES = {".md", ".txt", ".json", ".yaml", ".yml"}
DIRECTORY_TEXT_NAMES = {"LICENSE"}
DIRECTORY_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
DIRECTORY_SYSTEM_FILES = {".DS_Store", "Thumbs.db", "desktop.ini"}
DIRECTORY_MAX_FILES = 512
DIRECTORY_MAX_TEXT_BYTES = 256 * 1024
DIRECTORY_ICON = ".claude-plugin/icon.png"
DIRECTORY_ICON_MIN_PX, DIRECTORY_ICON_MAX_PX = 512, 2048
DIRECTORY_ICON_MAX_BYTES = 2 * 1024 * 1024
DIRECTORY_README_MIN_WORDS = 40
# Text like `$GITHUB_TOKEN` or `${KEY}` reads to the directory's scanner as a
# credential taken from the user's environment, and holds the version.
SHELL_VARIABLE = re.compile(r"\$\{?[A-Za-z_][A-Za-z0-9_]*")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

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

    # An empty version keeps the one checked in (a build from main, not a tag).
    if args.version:
        manifest["version"] = args.version
    if not manifest.get("version"):
        fail("plugin.json has no 'version' and none was given")
    write_json(args.output, manifest)


def manifest_version(args):
    version = read_json(args.manifest).get("version")
    if not version:
        fail(f"{args.manifest} has no 'version'")
    print(version)


def png_dimensions(path):
    with open(path, "rb") as image:
        header = image.read(24)
    if len(header) < 24 or header[:8] != PNG_SIGNATURE or header[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", header[16:24])


def readme_word_count(text):
    # The directory doesn't count words inside code blocks.
    prose = re.sub(r"^```.*?^```", " ", text, flags=re.MULTILINE | re.DOTALL)
    return len(re.findall(r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*", prose))


def verify_directory_plugin(args):
    root = Path(args.directory)
    problems = []

    files = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        if path.is_symlink():
            problems.append(f"{rel}: symbolic link; the directory needs regular files")
        elif path.name in DIRECTORY_SYSTEM_FILES or "__MACOSX" in path.parts:
            problems.append(f"{rel}: system file; the directory blocks it")
        elif path.is_file():
            files.append((path, rel))

    if len(files) > DIRECTORY_MAX_FILES:
        problems.append(f"{len(files)} files; the directory holds plugins over {DIRECTORY_MAX_FILES}")

    for path, rel in files:
        suffix = path.suffix.lower()
        if suffix in DIRECTORY_IMAGE_SUFFIXES:
            continue
        if suffix not in DIRECTORY_TEXT_SUFFIXES and path.name not in DIRECTORY_TEXT_NAMES:
            problems.append(
                f"{rel}: not Markdown, text, JSON, YAML, or an image; the directory "
                "holds it now and will refuse it from organizations that aren't Verified"
            )
            continue
        data = path.read_bytes()
        if len(data) >= DIRECTORY_MAX_TEXT_BYTES:
            problems.append(f"{rel}: {len(data)} bytes; the directory holds text files of 256 KiB or more")
        if b"\0" in data or data.startswith(b"#!"):
            problems.append(f"{rel}: looks like a program, not text")
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            problems.append(f"{rel}: not UTF-8 text")
            continue
        variable = SHELL_VARIABLE.search(text)
        if variable:
            problems.append(
                f"{rel}: '{variable.group(0)}' reads like a shell variable; the "
                "directory holds the plugin as 'Uses a credential from the user's machine'"
            )

    manifest_path = root / PLUGIN_MANIFEST_MEMBER
    if not manifest_path.is_file():
        problems.append(f"missing {PLUGIN_MANIFEST_MEMBER}")
    else:
        manifest = read_json(manifest_path)
        missing = [key for key in DIRECTORY_REQUIRED_KEYS if not manifest.get(key)]
        if missing:
            problems.append(f"{PLUGIN_MANIFEST_MEMBER} is missing {', '.join(missing)}")

    icon = root / DIRECTORY_ICON
    if not icon.is_file():
        problems.append(f"missing {DIRECTORY_ICON}; the listing icon locks on the first save")
    else:
        size = png_dimensions(icon)
        if size is None:
            problems.append(f"{DIRECTORY_ICON} is not a PNG")
        else:
            width, height = size
            if width != height or not DIRECTORY_ICON_MIN_PX <= width <= DIRECTORY_ICON_MAX_PX:
                problems.append(
                    f"{DIRECTORY_ICON} is {width}x{height}; the directory needs a square of "
                    f"{DIRECTORY_ICON_MIN_PX} to {DIRECTORY_ICON_MAX_PX} px"
                )
        if icon.stat().st_size >= DIRECTORY_ICON_MAX_BYTES:
            problems.append(f"{DIRECTORY_ICON} is 2 MB or more")

    readme = root / "README.md"
    if not readme.is_file():
        problems.append("missing README.md; the directory blocks a plugin without one")
    else:
        words = readme_word_count(readme.read_text(encoding="utf-8"))
        if words < DIRECTORY_README_MIN_WORDS:
            problems.append(f"README.md has {words} words outside code blocks; the directory needs {DIRECTORY_README_MIN_WORDS}")

    if not (root / "LICENSE").is_file():
        problems.append("missing LICENSE")

    mcp_config = root / ".mcp.json"
    if not mcp_config.is_file() or read_json(mcp_config) != EXPECTED_MCP_CONFIG:
        problems.append(".mcp.json must contain only the credential-free GetWhys HTTP server declaration")

    if problems:
        fail("the plugin folder breaks Claude directory rules:\n  " + "\n  ".join(problems))


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

    version = commands.add_parser("manifest-version")
    version.add_argument("manifest")
    version.set_defaults(run=manifest_version)

    directory_plugin = commands.add_parser("verify-directory-plugin")
    directory_plugin.add_argument("directory")
    directory_plugin.set_defaults(run=verify_directory_plugin)

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
