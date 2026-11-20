#!/usr/bin/env python3
"""Render and validate JSON metadata used by packaged release artifacts."""

import argparse
import html
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

# The Microsoft 365 Marketplace app's MCP connection may name only the public
# endpoint and a connection that Microsoft stores, never credentials.
M365_MCP_URL = "https://api.getwhys.io/mcp/org"
M365_SERVER_KEYS = {"mcpServerUrl", "authorization", "mcpToolDescription"}
M365_AUTH_KEYS = {"type", "referenceId"}
# Certification refuses a devPreview manifest once the connector uses
# DynamicClientRegistration, and asks for developer.contactInfo to be removed
# (policy 1140.4.1.1, 1.7.1 report, 2026-11-18). The manifest must name a public
# schema, which the build then validates it against.
M365_PUBLIC_SCHEMA = re.compile(
    r"https://developer\.microsoft\.com/en-us/json-schemas/teams/v(\d+\.\d+)/MicrosoftTeams\.schema\.json"
)
# "Developer name must be the same in the app manifest and AppSource" (Teams
# Store validation guidelines, App name, Must fix). AppSource shows the Partner
# Center publisher name: "by Get Whys Inc".
M365_PUBLISHER_NAME = "Get Whys Inc"
# Store text names Microsoft products in full the first time, and may shorten
# them after: "write the first reference in the app listing as Microsoft
# Teams" (guidelines, App descriptions, Must fix). Microsoft's reviewers apply
# the same rule to Copilot, and Microsoft is never "MS" or "MSFT".
M365_FIRST_MENTIONS = {
    "Copilot": re.compile(r"Microsoft\s+(?:365\s+)?Copilot$"),
    "Teams": re.compile(r"Microsoft\s+Teams$"),
}
M365_ABBREVIATION = re.compile(r"\b(?:MS|MSFT)\b")

# The Partner Center listing kept in packaging/m365/listing/. Limits are
# Partner Center's (its field lengths, read 2026-11-19) and the guidelines'
# Screenshots section.
M365_SUMMARY_MAX = 100
M365_DESCRIPTION_MAX = 10000
M365_MAX_SCREENSHOTS = 5
M365_SCREENSHOT_PX = (1366, 768)
M365_SCREENSHOT_MAX_BYTES = 1024 * 1024
M365_VIDEO_URL = re.compile(r"https://(?:www\.)?(?:youtube\.com|youtu\.be|vimeo\.com)/\S+")
# PNG chunks that carry text or EXIF (author, software, capture details). A
# committed screenshot stays public in git history, so it ships without them.
PNG_METADATA_CHUNKS = {b"tEXt", b"iTXt", b"zTXt", b"eXIf"}

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


def png_metadata_chunks(path):
    """Names of the text and EXIF chunks in a PNG."""
    data = Path(path).read_bytes()
    found, offset = set(), len(PNG_SIGNATURE)
    while offset + 8 <= len(data):
        length, kind = struct.unpack(">I4s", data[offset : offset + 8])
        if kind in PNG_METADATA_CHUNKS:
            found.add(kind.decode("ascii"))
        offset += 12 + length
    return sorted(found)


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


def m365_name_problems(label, texts):
    """Microsoft product names in store text, given in the order a reader sees it."""
    text = "\n".join(texts)
    problems = []
    for product, full_name in M365_FIRST_MENTIONS.items():
        first = re.search(rf"\b{product}\b", text)
        if first and not full_name.search(text[: first.end()]):
            problems.append(
                f"{label}: the first mention of {product} must name it in full "
                f"(e.g. 'Microsoft {product}'): ...{text[max(0, first.start() - 40) : first.end()]!r}"
            )
    abbreviation = M365_ABBREVIATION.search(text)
    if abbreviation:
        problems.append(f"{label}: write 'Microsoft', not {abbreviation.group(0)!r}")
    return problems


def m365_manifest_texts(manifest):
    """The manifest text a store customer reads, in display order."""
    texts = [
        (manifest.get("name") or {}).get("short", ""),
        (manifest.get("name") or {}).get("full", ""),
        (manifest.get("description") or {}).get("short", ""),
        (manifest.get("description") or {}).get("full", ""),
    ]
    for connector in manifest.get("agentConnectors") or []:
        texts += [connector.get("displayName", ""), connector.get("description", "")]
    return texts


def check_m365_manifest(manifest, path):
    """Fail unless the source manifest is safe to publish and to build from."""
    if not manifest.get("id"):
        fail(f"{path} has no 'id'; it must keep the live app's id")
    if "agentSkills" in manifest:
        fail(f"{path} must not list agentSkills; the build adds one per skills/<name>/")

    schema = M365_PUBLIC_SCHEMA.fullmatch(manifest.get("$schema", ""))
    if not schema or manifest.get("manifestVersion") != schema.group(1):
        fail(
            f"{path} must use a public manifest schema (e.g. v1.30), with $schema and "
            f"manifestVersion naming the same version; Microsoft certification "
            f"rejects devPreview for this app"
        )
    developer = manifest.get("developer") or {}
    if "contactInfo" in developer:
        fail(f"{path} must not have developer.contactInfo; Microsoft certification rejects it")
    if developer.get("name") != M365_PUBLISHER_NAME:
        fail(
            f"{path}: developer.name must be {M365_PUBLISHER_NAME!r}, the Partner Center "
            f"publisher name; Microsoft certification requires the two to match"
        )
    problems = m365_name_problems(path, m365_manifest_texts(manifest))
    if problems:
        fail("\n  ".join(problems))

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


def verify_m365_listing(args):
    """Check the Partner Center listing in packaging/m365/listing/ (see its README)."""
    root = Path(args.listing)
    listing = read_json(root / "listing.json")
    developer = read_json(args.manifest).get("developer") or {}
    problems = []

    summary = listing.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        problems.append("summary is missing")
        summary = ""
    elif "\n" in summary or len(summary) > M365_SUMMARY_MAX:
        problems.append(
            f"summary must be one line of at most {M365_SUMMARY_MAX} characters "
            f"(Partner Center's limit); it has {len(summary)}"
        )

    description_text = ""
    description_path = root / str(listing.get("description", ""))
    if not listing.get("description") or not description_path.is_file():
        problems.append(f"description file {listing.get('description')!r} is missing")
    else:
        description = description_path.read_text(encoding="utf-8").strip()
        if not description:
            problems.append(f"{description_path.name} is empty")
        elif len(description) > M365_DESCRIPTION_MAX:
            problems.append(
                f"{description_path.name} has {len(description)} characters; "
                f"Partner Center takes {M365_DESCRIPTION_MAX}"
            )
        description_text = html.unescape(re.sub(r"<[^>]+>", " ", description))

    # Partner Center needs at least one screenshot, but this folder may hold
    # none: the live ones stay in Partner Center until replacements made for
    # publication are committed here (see the README).
    screenshots = listing.get("screenshots") or []
    if len(screenshots) > M365_MAX_SCREENSHOTS:
        problems.append(f"{len(screenshots)} screenshots; Partner Center takes {M365_MAX_SCREENSHOTS}")
    listed = set()
    captions = []
    for shot in screenshots:
        file = shot.get("file", "")
        path = root / file
        listed.add(path.resolve())
        if not path.is_file():
            problems.append(f"screenshot {file!r} is missing")
            continue
        size = png_dimensions(path)
        if size is None:
            problems.append(f"{file} is not a PNG")
        else:
            if size != M365_SCREENSHOT_PX:
                problems.append(f"{file} is {size[0]}x{size[1]}; screenshots must be exactly 1366x768")
            metadata = png_metadata_chunks(path)
            if metadata:
                problems.append(
                    f"{file} carries metadata ({', '.join(metadata)}); strip it before "
                    f"committing, e.g. exiftool -all= {path.name}"
                )
        if path.stat().st_size > M365_SCREENSHOT_MAX_BYTES:
            problems.append(f"{file} is larger than 1,024 KB")
        if not str(shot.get("caption", "")).strip():
            problems.append(f"{file} has no caption")
        captions.append(str(shot.get("caption", "")))
    for path in sorted((root / "screenshots").glob("*")):
        if path.resolve() not in listed:
            problems.append(f"screenshots/{path.name} isn't listed in listing.json")

    video = listing.get("videoUrl")
    if video and not M365_VIDEO_URL.fullmatch(video):
        problems.append(f"videoUrl {video!r} must be a YouTube or Vimeo link")

    if listing.get("eulaUrl") != developer.get("termsOfUseUrl"):
        problems.append(
            f"eulaUrl {listing.get('eulaUrl')!r} must equal the manifest's "
            f"developer.termsOfUseUrl {developer.get('termsOfUseUrl')!r}"
        )
    if listing.get("privacyUrl") != developer.get("privacyUrl"):
        problems.append(
            f"privacyUrl {listing.get('privacyUrl')!r} must equal the manifest's "
            f"developer.privacyUrl {developer.get('privacyUrl')!r}"
        )
    if not str(listing.get("supportUrl", "")).startswith("https://"):
        problems.append("supportUrl must be an https URL; Partner Center doesn't take an email address")

    problems += m365_name_problems("listing", [summary, description_text, *captions])

    if problems:
        fail("the Microsoft 365 listing breaks Partner Center rules:\n  " + "\n  ".join(problems))


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

    m365_listing = commands.add_parser("verify-m365-listing")
    m365_listing.add_argument("listing")
    m365_listing.add_argument("manifest")
    m365_listing.set_defaults(run=verify_m365_listing)

    return parser.parse_args()


def main():
    args = parse_args()
    args.run(args)


if __name__ == "__main__":
    main()
