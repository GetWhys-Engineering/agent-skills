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

# The Microsoft 365 Marketplace app's MCP connection may name only the public
# endpoint and a connection that Microsoft stores, never credentials.
M365_MCP_URL = "https://api.getwhys.io/mcp/org"
M365_SERVER_KEYS = {"mcpServerUrl", "authorization", "mcpToolDescription"}
M365_AUTH_KEYS = {"type", "referenceId"}

# The installable Microsoft 365 declarative-agent package is intentionally
# separate from the existing agentConnectors Marketplace package above.
M365_AGENT_ROOT_FILES = {
    "manifest.json",
    "declarativeAgent.json",
    "ai-plugin.json",
    "Color.png",
    "Outline.png",
}
M365_AGENT_SKILL_NAME = "validate-gtm-output"
M365_AGENT_SKILL_FOLDER = f"skills/{M365_AGENT_SKILL_NAME}"
M365_AGENT_MAX_SKILL_FILES = 350
M365_AGENT_MAX_SKILL_DIRECTORY_DEPTH = 3
M365_AGENT_MAX_PACKAGE_BYTES = 10 * 1024 * 1024
M365_AGENT_APP_SCHEMA = (
    "https://developer.microsoft.com/json-schemas/teams/v1.30/MicrosoftTeams.schema.json"
)
M365_AGENT_DA_SCHEMA = (
    "https://developer.microsoft.com/json-schemas/copilot/declarative-agent/v1.9/schema.json"
)
M365_AGENT_PLUGIN_SCHEMA = (
    "https://developer.microsoft.com/json-schemas/copilot/plugin/v2.4/schema.json"
)
M365_AGENT_PLACEHOLDERS = {
    "${{TEAMS_APP_ID}}": "app_id",
    "${{GETWHYS_DCR_AUTH_ID}}": "auth_id",
    "${{APP_VERSION}}": "version",
    "${{APP_NAME_SUFFIX}}": "app_name_suffix",
}

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
    """Map release tag vX.Y.Z to Microsoft app version (X+1).Y.Z.

    Both Microsoft 365 packages, the Marketplace app and the Copilot agent, use
    this mapping, so one tag ships them at the same version. Microsoft requires
    every upload to be higher than the last and rejects a version that starts
    with 0, and the Marketplace app was published at 1.0.3 before this repo
    built it.
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
            check_microsoft_skills(archive, manifest.get("agentSkills", []))
    except (OSError, zipfile.BadZipFile) as error:
        fail(f"cannot read package {args.archive}: {error}")

    if not args.cowork:
        check_m365_manifest(
            {key: value for key, value in manifest.items() if key != "agentSkills"},
            "packaged manifest.json",
        )
    for icon in (manifest.get("icons") or {}).values():
        if icon not in members:
            fail(f"icon {icon!r} named in manifest.json is missing from the package")


def check_microsoft_skills(archive, entries, *, declarative_agent=False):
    """Share skill hygiene while retaining each Microsoft surface's limits."""
    members = {info.filename: info for info in archive.infolist()}
    for name in members:
        parts = name.rstrip("/").split("/")
        if any(part.startswith(".") or part == "__MACOSX" for part in parts) or "\\" in name:
            fail(f"hidden or macOS metadata entry {name!r} in the package")

    folders = [
        entry.get("folder", "").removeprefix("./").rstrip("/")
        for entry in entries
    ]
    maximum_skills = 8 if declarative_agent else M365_MAX_SKILLS
    if not folders or len(folders) > maximum_skills:
        fail(f"package must contain between 1 and {maximum_skills} Microsoft skills")
    if len(folders) != len(set(folders)):
        fail("Microsoft skills list a folder twice")

    if declarative_agent:
        if sum(info.file_size for info in members.values()) > M365_AGENT_MAX_PACKAGE_BYTES:
            fail("Microsoft 365 agent package exceeds the 10 MB limit")
        skill_file_count = sum(
            not info.is_dir() and any(member.startswith(f"{folder}/") for folder in folders)
            for member, info in members.items()
        )
        if skill_file_count > M365_AGENT_MAX_SKILL_FILES:
            fail(f"Microsoft 365 agent skills exceed {M365_AGENT_MAX_SKILL_FILES} files")

    for folder in folders:
        if not folder or folder.startswith("/") or any(
            part in ("", ".", "..") for part in folder.split("/")
        ):
            fail(f"unsafe Microsoft skill folder {folder!r}")
        member = f"{folder}/SKILL.md"
        if member not in members:
            fail(f"Microsoft skill folder {folder!r} has no SKILL.md in the package")
        text = archive.read(member).decode("utf-8")
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
        if not declarative_agent and len(companions) > M365_MAX_COMPANIONS:
            fail(f"{folder} has {len(companions)} companion files (max {M365_MAX_COMPANIONS})")
        if (
            not declarative_agent
            and sum(info.file_size for info in companions) > M365_MAX_COMPANION_TOTAL
        ):
            fail(f"{folder} companion files exceed 10 MB in total")
        for info in companions:
            base = info.filename.split("/")[-1]
            if not declarative_agent and info.file_size > M365_MAX_COMPANION_BYTES:
                fail(f"{info.filename} is larger than 5 MB")
            relative_parts = info.filename[len(folder) + 1:].split("/")
            if (
                declarative_agent
                and len(relative_parts) - 1 > M365_AGENT_MAX_SKILL_DIRECTORY_DEPTH
            ):
                fail(f"{info.filename} exceeds skill directory depth 3")
            if "\\" in info.filename or not M365_SAFE_FILE_NAME.fullmatch(base):
                fail(f"{info.filename} has characters Microsoft rejects")
            if WINDOWS_RESERVED.fullmatch(base):
                fail(f"{info.filename} uses a Windows reserved name")


def substitute_m365_agent(value, replacements):
    if isinstance(value, dict):
        return {
            key: substitute_m365_agent(item, replacements)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [substitute_m365_agent(item, replacements) for item in value]
    if isinstance(value, str):
        for placeholder, replacement in replacements.items():
            value = value.replace(placeholder, replacement)
    return value


def check_m365_agent_manifests(manifest, agent, plugin, label):
    """Validate the package wiring and the security-sensitive MCP settings."""
    if manifest.get("$schema") != M365_AGENT_APP_SCHEMA:
        fail(f"{label}: manifest.json must use the numbered v1.30 schema")
    if manifest.get("manifestVersion") != "1.30":
        fail(f"{label}: manifest.json manifestVersion must be 1.30")
    if not re.fullmatch(
        r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}",
        manifest.get("id", ""),
    ):
        fail(f"{label}: manifest.json id must be a provisioned GUID")
    if not re.fullmatch(r"\d+\.\d+\.\d+", manifest.get("version", "")):
        fail(f"{label}: manifest.json version must be semantic X.Y.Z")
    if manifest["version"].split(".")[0] == "0":
        fail(
            f"{label}: manifest.json version must be 1.0.0 or higher; Microsoft's "
            "package validation rejects a version that starts with 0"
        )
    if "agentConnectors" in manifest:
        fail(f"{label}: the declarative-agent package must not declare agentConnectors")
    refs = ((manifest.get("copilotAgents") or {}).get("declarativeAgents") or [])
    if refs != [{"id": "getwhysBuyerIntelligence", "file": "declarativeAgent.json"}]:
        fail(f"{label}: manifest.json must reference declarativeAgent.json exactly once")

    if agent.get("$schema") != M365_AGENT_DA_SCHEMA or agent.get("version") != "v1.9":
        fail(f"{label}: declarativeAgent.json must use schema v1.9")
    if agent.get("actions") != [{"id": "getwhysMcpAction", "file": "ai-plugin.json"}]:
        fail(f"{label}: declarativeAgent.json must reference ai-plugin.json exactly once")
    if any(
        str(skill.get("folder", "")).startswith("./")
        for skill in agent.get("agent_skills") or []
        if isinstance(skill, dict)
    ):
        fail(
            f"{label}: declarativeAgent.json skill folders must not start with './'; "
            "Microsoft's package validation can't resolve SKILL.md through it"
        )
    if agent.get("agent_skills") != [{"folder": M365_AGENT_SKILL_FOLDER}]:
        fail(
            f"{label}: declarativeAgent.json must reference the bundled "
            f"{M365_AGENT_SKILL_NAME} skill exactly once, as "
            f"{{\"folder\": \"{M365_AGENT_SKILL_FOLDER}\"}}"
        )
    if not agent.get("instructions"):
        fail(f"{label}: declarativeAgent.json has no instructions")

    if plugin.get("$schema") != M365_AGENT_PLUGIN_SCHEMA:
        fail(f"{label}: ai-plugin.json must use plugin schema v2.4")
    if plugin.get("schema_version") != "v2.4":
        fail(f"{label}: ai-plugin.json schema_version must be v2.4")
    if plugin.get("functions") != []:
        fail(f"{label}: ai-plugin.json functions must stay empty for dynamic discovery")
    runtimes = plugin.get("runtimes") or []
    if len(runtimes) != 1:
        fail(f"{label}: ai-plugin.json must declare exactly one runtime")
    runtime = runtimes[0]
    if runtime.get("type") != "RemoteMCPServer":
        fail(f"{label}: ai-plugin.json runtime must be RemoteMCPServer")
    spec = runtime.get("spec") or {}
    if spec.get("url") != M365_MCP_URL:
        fail(f"{label}: ai-plugin.json must use {M365_MCP_URL}")
    if "mcp_tool_description" in spec:
        fail(f"{label}: omit mcp_tool_description to keep dynamic tool discovery")
    if runtime.get("run_for_functions") != ["*"]:
        fail(f"{label}: RemoteMCPServer must dispatch all discovered tools with ['*']")
    auth = runtime.get("auth") or {}
    for value, allowed, where in (
        (runtime, {"type", "spec", "run_for_functions", "auth"}, "runtime"),
        (spec, {"url"}, "spec"),
        (auth, {"type", "reference_id"}, "auth"),
    ):
        extra = set(value) - allowed
        if extra:
            fail(f"{label}: unexpected {where} keys {sorted(extra)}")
    if auth.get("type") != "OAuthPluginVault":
        fail(f"{label}: declarative-agent MCP auth must use OAuthPluginVault")
    reference_id = auth.get("reference_id", "")
    if not reference_id or reference_id == "shared_getwhysmcp":
        fail(
            f"{label}: reference_id must be a provisioned DCR auth-configuration ID, "
            "never the connector's ConnectionVault reference"
        )
    if "${{" in reference_id:
        fail(f"{label}: unresolved DCR auth-configuration placeholder")

    serialized = json.dumps([manifest, agent, plugin])
    if "${{" in serialized:
        fail(f"{label}: unresolved ${{{{...}}}} placeholder")
    serialized = serialized.lower()
    forbidden = ("client_secret", "access_token", "refresh_token", "authorization_code")
    found = [name for name in forbidden if name in serialized]
    if found:
        fail(f"{label}: manifests contain credential-bearing fields {found}")


def render_m365_agent(args):
    source = Path(args.source)
    output = Path(args.output)
    if not source.is_dir():
        fail(f"Microsoft 365 agent source directory does not exist: {source}")
    if args.auth_id == "shared_getwhysmcp":
        fail("the declarative agent cannot reuse the ConnectionVault reference")
    if not args.auth_id.strip():
        fail("GETWHYS_DCR_AUTH_ID is empty; provision DCR before packaging")
    args.version = m365_version(args.version)

    replacements = {
        placeholder: str(getattr(args, name))
        for placeholder, name in M365_AGENT_PLACEHOLDERS.items()
    }
    rendered = {}
    for filename in ("manifest.json", "declarativeAgent.json", "ai-plugin.json"):
        rendered[filename] = substitute_m365_agent(
            read_json(source / filename), replacements
        )

    check_m365_agent_manifests(
        rendered["manifest.json"],
        rendered["declarativeAgent.json"],
        rendered["ai-plugin.json"],
        "rendered Microsoft 365 agent",
    )
    output.mkdir(parents=True, exist_ok=True)
    for filename, value in rendered.items():
        write_json(output / filename, value)
    print(args.version)


M365_AGENT_PROD_ENV_KEYS = {
    "TEAMSFX_ENV", "APP_NAME_SUFFIX", "APP_VERSION", "AGENT_SCOPE",
    "TEAMS_APP_ID", "TEAMS_APP_TENANT_ID", "GETWHYS_DCR_AUTH_ID",
    "M365_TITLE_ID", "M365_APP_ID", "SHARE_LINK",
    "M365_PUBLISHED_TITLE_ID", "M365_PUBLISHED_APP_ID",
}


def check_m365_agent_env(args):
    """The committed production env file holds only public Microsoft IDs."""
    label = args.path
    values = {}
    for number, line in enumerate(Path(args.path).read_text().splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if not sep:
            fail(f"{label}:{number}: expected KEY=value")
        if key not in M365_AGENT_PROD_ENV_KEYS:
            fail(
                f"{label}:{number}: unexpected key {key!r}; this committed file holds "
                "only public Microsoft IDs, and secrets belong in env/.env.prod.user"
            )
        values[key] = value
    if values.get("TEAMSFX_ENV") != "prod" or values.get("APP_NAME_SUFFIX"):
        fail(f"{label}: must set TEAMSFX_ENV=prod and an empty APP_NAME_SUFFIX")
    app_id = values.get("TEAMS_APP_ID", "")
    auth_id = values.get("GETWHYS_DCR_AUTH_ID", "")
    if bool(app_id) != bool(auth_id):
        fail(f"{label}: set TEAMS_APP_ID and GETWHYS_DCR_AUTH_ID together")
    if app_id and not re.fullmatch(
        r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", app_id
    ):
        fail(f"{label}: TEAMS_APP_ID must be a GUID")
    if auth_id == "shared_getwhysmcp":
        fail(f"{label}: the agent cannot reuse the Marketplace app's connection reference")


def verify_m365_agent_package(args):
    repository_root = Path(__file__).resolve().parent.parent
    skill_source = repository_root / "skills" / M365_AGENT_SKILL_NAME
    if not skill_source.is_dir():
        fail(f"canonical Microsoft 365 agent skill is missing: {skill_source}")
    skill_files = sorted(path for path in skill_source.rglob("*") if path.is_file())
    expected_skill_members = {
        f"{M365_AGENT_SKILL_FOLDER}/{path.relative_to(skill_source).as_posix()}"
        for path in skill_files
    }
    expected_members = M365_AGENT_ROOT_FILES | expected_skill_members

    try:
        with zipfile.ZipFile(args.archive) as archive:
            members = {
                info.filename
                for info in archive.infolist()
                if not info.is_dir()
            }
            if members != expected_members:
                missing = sorted(expected_members - members)
                extra = sorted(members - expected_members)
                fail(
                    f"Microsoft 365 agent package has wrong files; "
                    f"missing={missing}, extra={extra}"
                )
            for source_path in skill_files:
                member = (
                    f"{M365_AGENT_SKILL_FOLDER}/"
                    f"{source_path.relative_to(skill_source).as_posix()}"
                )
                if archive.read(member) != source_path.read_bytes():
                    fail(f"packaged {member} differs from the canonical skill source")
            manifest = read_member_json(archive, "manifest.json")
            agent = read_member_json(archive, "declarativeAgent.json")
            check_microsoft_skills(
                archive, agent.get("agent_skills", []), declarative_agent=True
            )
            plugin = read_member_json(archive, "ai-plugin.json")
            for icon in ("Color.png", "Outline.png"):
                data = archive.read(icon)
                if not data.startswith(PNG_SIGNATURE):
                    fail(f"packaged {icon} is not a PNG")
    except (OSError, zipfile.BadZipFile) as error:
        fail(f"cannot read Microsoft 365 agent package {args.archive}: {error}")

    check_m365_agent_manifests(
        manifest, agent, plugin, "packaged Microsoft 365 agent"
    )


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
    m365_package.set_defaults(run=verify_m365_package, cowork=False)

    cowork_package = commands.add_parser("verify-cowork-package")
    cowork_package.add_argument("archive")
    cowork_package.set_defaults(run=verify_m365_package, cowork=True)

    m365_agent_render = commands.add_parser("render-m365-agent")
    m365_agent_render.add_argument("source")
    m365_agent_render.add_argument("output")
    m365_agent_render.add_argument("app_id")
    m365_agent_render.add_argument("auth_id")
    m365_agent_render.add_argument("version")
    m365_agent_render.add_argument("app_name_suffix")
    m365_agent_render.set_defaults(run=render_m365_agent)

    m365_agent_env = commands.add_parser("check-m365-agent-env")
    m365_agent_env.add_argument("path")
    m365_agent_env.set_defaults(run=check_m365_agent_env)

    m365_agent_package = commands.add_parser("verify-m365-agent-package")
    m365_agent_package.add_argument("archive")
    m365_agent_package.set_defaults(run=verify_m365_agent_package)

    return parser.parse_args()


def main():
    args = parse_args()
    args.run(args)


if __name__ == "__main__":
    main()
