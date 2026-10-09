#!/usr/bin/env python3
"""Build a portable OpenAI upload without packaging repository/private state."""

import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parent.parent
SCHEMA_ROOT = "https://agent-plugins.org/schemas/1.0.0/"
IGNORED = {".DS_Store", "__MACOSX", "__pycache__", ".git", "node_modules"}
MANIFEST_KEYS = {
    "$schema", "name", "version", "description", "author", "homepage",
    "repository", "license", "keywords", "extensions",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def build():
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    require(isinstance(manifest, dict), "plugin.json must be an object")
    require(set(manifest) <= MANIFEST_KEYS, "plugin.json has non-portable fields")
    require(manifest.get("$schema") == SCHEMA_ROOT + "plugin.schema.json",
            "plugin.json must declare Agent Plugins 1.0.0")
    name = manifest.get("name", "")
    require(isinstance(name, str) and len(name) <= 64 and
            re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name),
            "plugin name must be lowercase kebab-case, at most 64 characters")
    version = os.environ.get("VERSION", manifest.get("version", ""))
    version = version.removeprefix("v")
    require(re.fullmatch(
        r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
        r"(?:-(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)"
        r"(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*)?"
        r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?", version),
        "VERSION must be a semantic version, optionally prefixed with v")
    manifest["version"] = version
    # An empty release_notes string would clear the dashboard's saved notes.
    notes = os.environ.get("RELEASE_NOTES", "").strip()
    if notes:
        extension = manifest.setdefault("extensions", {}).setdefault("com.openai", {})
        extension.setdefault("publication", {})["release_notes"] = notes
    openai = manifest.get("extensions", {}).get("com.openai", {})
    require(openai.get("apps") is None,
            "public uploads must use mcp.json, not an apps binding")
    config = json.loads((ROOT / "mcp.json").read_text(encoding="utf-8"))
    require(config == {
        "$schema": SCHEMA_ROOT + "mcp.schema.json",
        "mcpServers": {"getwhys": {
            "type": "streamable-http", "url": "https://api.getwhys.io/mcp/org",
        }},
    }, "mcp.json must contain only the credential-free portable GetWhys endpoint")

    files = {}

    def add_file(path):
        require(not path.is_symlink(), f"symlinks cannot be packaged: {path}")
        require(path.is_file(), f"missing package file: {path}")
        require(path.resolve().is_relative_to(ROOT), f"file escapes plugin root: {path}")
        member = path.relative_to(ROOT).as_posix()
        require(not any(part in IGNORED or part.startswith(".env")
                        for part in path.relative_to(ROOT).parts),
                f"private or generated file cannot be packaged: {member}")
        files[member] = path.read_bytes()

    for filename in ("plugin.json", "mcp.json", "LICENSE"):
        add_file(ROOT / filename)
    files["plugin.json"] = (json.dumps(manifest, indent=2) + "\n").encode()

    skills = ROOT / "skills"
    require(not skills.is_symlink(), "skills/ cannot be a symlink")
    count = 0
    for skill in sorted(skills.iterdir()):
        require(not skill.is_symlink(), f"skill cannot be a symlink: {skill}")
        if not skill.is_dir():
            continue
        require((skill / "SKILL.md").is_file(), f"missing {skill.name}/SKILL.md")
        count += 1
        for path in sorted(skill.rglob("*")):
            if any(part in IGNORED for part in path.relative_to(skill).parts):
                continue
            require(not path.is_symlink(), f"symlinks cannot be packaged: {path}")
            if path.is_file():
                add_file(path)
    require(count > 0, "no skills found")

    interface = openai.get("interface", {})
    references = [interface.get(key) for key in
                  ("logo", "logoDark", "composerIcon", "composerIconDark")]
    references.extend(interface.get("screenshots", []))
    for reference in filter(None, references):
        require(isinstance(reference, str) and reference.startswith("./"),
                "asset references must start with ./")
        parts = PurePosixPath(reference).parts
        require(bool(parts) and ".." not in parts and "\\" not in reference,
                f"invalid asset reference: {reference}")
        require(parts[0] not in {"plugin.json", "mcp.json", "skills", ".app.json"}
                and not parts[0].startswith("."), f"invalid asset location: {reference}")
        asset = ROOT.joinpath(*parts)
        require(not any(parent.is_symlink() for parent in asset.parents
                        if parent.is_relative_to(ROOT)), "asset path contains a symlink")
        add_file(asset)

    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    output = dist / "getwhys-openai.zip"
    with tempfile.NamedTemporaryFile(dir=dist, suffix=".zip", delete=False) as temp:
        temporary = Path(temp.name)
    try:
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
            for member, data in sorted(files.items()):
                archive.writestr(f"{name}/{member}", data)
        with zipfile.ZipFile(temporary) as archive:
            require(archive.testzip() is None, "ZIP integrity check failed")
            require(set(archive.namelist()) == {f"{name}/{f}" for f in files},
                    "ZIP inventory mismatch")
            require(json.loads(archive.read(f"{name}/plugin.json")) == manifest,
                    "packaged manifest mismatch")
            require(json.loads(archive.read(f"{name}/mcp.json")) == config,
                    "packaged MCP configuration mismatch")
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Built {output} (version {version}, {count} skill(s), {len(files)} files).")
    review = openai.get("review", {})
    publication = openai.get("publication", {})
    gaps = []
    if not interface.get("logo"):
        gaps.append("listing icon")
    if not publication.get("release_notes"):
        gaps.append("release notes")
    if gaps:
        print("Draft package; submission still needs: " + "; ".join(gaps) + ".")
    cases = review.get("test_cases", {})
    if (not review.get("demo_recording_url") or len(cases.get("positive", [])) != 5
            or len(cases.get("negative", [])) != 3):
        print("Review cases and demo recording are not in the package: an update reuses "
              "the ones saved in the dashboard; an initial MCP review needs all of them.")
    print("Authentication, reviewer access, verification, and scans must be checked in the portal.")


if __name__ == "__main__":
    try:
        build()
    except (ValueError, OSError, TypeError, AttributeError) as error:
        raise SystemExit(f"FAIL: {error}")
