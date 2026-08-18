#!/usr/bin/env python3
"""Build the Shuku agent skills registry from configured GitHub repositories."""

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import yaml

try:
    from .validate_agent_skills import (
        RegistryValidationError,
        _validate_ref,
        validate_registry,
    )
except ImportError:  # Support direct execution as a script.
    from validate_agent_skills import RegistryValidationError, _validate_ref, validate_registry


REPOSITORY_SLUG = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
REQUIRED_MANIFEST_FIELDS = (
    "schema_version",
    "name",
    "version",
    "repository",
    "ref",
    "path",
)


class BuildError(RuntimeError):
    """Raised when skill discovery or metadata validation fails."""


def _run_git(arguments: Sequence[str], cwd: Optional[Path] = None) -> str:
    command = ["git"] + list(arguments)
    try:
        result = subprocess.run(
            command,
            cwd=str(cwd) if cwd else None,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
    except FileNotFoundError as exc:
        raise BuildError("Git is required to resolve remote skill repositories") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout).strip()
        raise BuildError(f"Git command failed ({' '.join(command)}): {detail}") from exc
    return result.stdout.strip()


def _validate_repository_slug(value: Any, location: str) -> str:
    if not isinstance(value, str) or not REPOSITORY_SLUG.fullmatch(value):
        raise BuildError(f"{location} must use the 'owner/repository' format")
    if value.split("/", 1)[0] != "reduct-shuku":
        raise BuildError(f"{location} must belong to the reduct-shuku organization")
    return value


def _normalize_relative_path(value: Any, location: str) -> str:
    if not isinstance(value, str) or not value:
        raise BuildError(f"{location} must be a non-empty relative POSIX path")
    if "\\" in value or value.startswith("/"):
        raise BuildError(f"{location} must be a relative POSIX path")
    if value == ".":
        return value
    parts = value.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise BuildError(f"{location} must not contain empty, '.' or '..' segments")
    return "/".join(parts)


def _read_json_text(text: str, location: str) -> Dict[str, Any]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise BuildError(f"{location} is not valid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise BuildError(f"{location} must contain a JSON object")
    return value


def _read_json_file(path: Path, location: str) -> Dict[str, Any]:
    try:
        return _read_json_text(path.read_text(encoding="utf-8"), location)
    except FileNotFoundError as exc:
        raise BuildError(f"{location} does not exist") from exc
    except (OSError, UnicodeError) as exc:
        raise BuildError(f"Cannot read {location}: {exc}") from exc


def _parse_frontmatter(text: str, location: str) -> Dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise BuildError(f"{location} must start with YAML frontmatter")
    closing_index = next(
        (index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"),
        None,
    )
    if closing_index is None:
        raise BuildError(f"{location} has unterminated YAML frontmatter")
    yaml_text = "\n".join(lines[1:closing_index])
    try:
        frontmatter = yaml.safe_load(yaml_text)
    except yaml.YAMLError as exc:
        raise BuildError(f"{location} has invalid YAML frontmatter: {exc}") from exc
    if not isinstance(frontmatter, dict):
        raise BuildError(f"{location} frontmatter must be a YAML mapping")
    result = {}
    for field in ("name", "description"):
        value = frontmatter.get(field)
        if not isinstance(value, str) or not value.strip():
            raise BuildError(f"{location} frontmatter.{field} must be a non-empty string")
        result[field] = value.strip()
    return result


class SourceRepository:
    def __init__(self, slug: str, path: Path, remote: bool):
        self.slug = slug
        self.path = path
        self.remote = remote
        self._commits = {}

    def read_worktree(self, relative_path: str) -> str:
        path = self.path.joinpath(*relative_path.split("/"))
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise BuildError(f"{self.slug}:{relative_path} does not exist") from exc
        except (OSError, UnicodeError) as exc:
            raise BuildError(f"Cannot read {self.slug}:{relative_path}: {exc}") from exc

    def read_at_ref(self, ref: str, relative_path: str) -> str:
        if not self.remote:
            return self.read_worktree(relative_path)
        if ref not in self._commits:
            _run_git(["fetch", "--quiet", "--depth", "1", "origin", ref], cwd=self.path)
            self._commits[ref] = _run_git(["rev-parse", "FETCH_HEAD"], cwd=self.path)
        return _run_git(
            ["show", f"{self._commits[ref]}:{relative_path}"], cwd=self.path
        )


def _resolve_local_repository(source_root: Path, slug: str) -> Path:
    owner, repository = slug.split("/", 1)
    candidates = (source_root / owner / repository, source_root / repository)
    for candidate in candidates:
        if candidate.is_dir():
            return candidate.resolve()
    raise BuildError(
        f"Local source for {slug} was not found under {source_root.resolve()}"
    )


def _materialize_repository(
    slug: str, source_root: Optional[Path], clone_root: Path
) -> SourceRepository:
    if source_root is not None:
        return SourceRepository(
            slug, _resolve_local_repository(source_root.resolve(), slug), remote=False
        )
    destination = clone_root / slug.replace("/", "--")
    _run_git(
        [
            "clone",
            "--quiet",
            "--depth",
            "1",
            f"https://github.com/{slug}.git",
            str(destination),
        ]
    )
    return SourceRepository(slug, destination, remote=True)


def _load_sources(sources_path: Path) -> List[Dict[str, str]]:
    config = _read_json_file(sources_path, str(sources_path))
    if config.get("schema_version") != 1:
        raise BuildError("registry/sources.json schema_version must equal 1")
    if set(config) != {"schema_version", "sources"}:
        raise BuildError("registry/sources.json must contain only schema_version and sources")
    raw_sources = config.get("sources")
    if not isinstance(raw_sources, list) or not raw_sources:
        raise BuildError("registry/sources.json sources must be a non-empty array")

    sources = []
    seen_repositories = set()
    for index, raw_source in enumerate(raw_sources):
        location = f"sources[{index}]"
        if not isinstance(raw_source, dict):
            raise BuildError(f"{location} must be a JSON object")
        if set(raw_source) != {"repository", "mode", "path"}:
            raise BuildError(f"{location} must contain repository, mode, and path")
        repository = _validate_repository_slug(
            raw_source.get("repository"), f"{location}.repository"
        )
        if repository in seen_repositories:
            raise BuildError(f"Duplicate source repository: {repository}")
        seen_repositories.add(repository)
        mode = raw_source.get("mode")
        if mode not in ("skills-directory", "repository-skill"):
            raise BuildError(f"{location}.mode is not supported: {mode!r}")
        path = _normalize_relative_path(raw_source.get("path"), f"{location}.path")
        if mode == "repository-skill" and path != ".":
            raise BuildError(f"{location}.path must equal '.' for repository-skill")
        sources.append({"repository": repository, "mode": mode, "path": path})
    return sources


def _join_posix(*parts: str) -> str:
    normalized = [part.strip("/") for part in parts if part not in ("", ".")]
    return "/".join(normalized) or "."


def _discover_skill_paths(repository: SourceRepository, source: Dict[str, str]) -> List[str]:
    if source["mode"] == "repository-skill":
        candidates = [source["path"]]
    else:
        root = repository.path.joinpath(*source["path"].split("/"))
        if not root.is_dir():
            raise BuildError(f"{source['repository']}:{source['path']} is not a directory")
        candidates = []
        for child in sorted(root.iterdir(), key=lambda item: item.name):
            if not child.is_dir():
                continue
            has_skill = (child / "SKILL.md").is_file()
            has_manifest = (child / "shuku.json").is_file()
            if has_skill != has_manifest:
                raise BuildError(
                    f"{source['repository']}:{_join_posix(source['path'], child.name)} "
                    "must contain both SKILL.md and shuku.json"
                )
            if has_skill:
                candidates.append(_join_posix(source["path"], child.name))
        if not candidates:
            raise BuildError(f"{source['repository']}:{source['path']} contains no skills")

    for skill_path in candidates:
        directory = repository.path if skill_path == "." else repository.path.joinpath(
            *skill_path.split("/")
        )
        if not (directory / "SKILL.md").is_file() or not (directory / "shuku.json").is_file():
            raise BuildError(
                f"{source['repository']}:{skill_path} must contain both SKILL.md and shuku.json"
            )
    return candidates


def _validate_manifest(
    manifest: Dict[str, Any], slug: str, actual_path: str, location: str
) -> None:
    missing = [field for field in REQUIRED_MANIFEST_FIELDS if field not in manifest]
    if missing:
        raise BuildError(f"{location} is missing required field(s): {', '.join(missing)}")
    if manifest["schema_version"] != 1:
        raise BuildError(f"{location}.schema_version must equal 1")
    for field in ("name", "version", "repository", "ref", "path"):
        if not isinstance(manifest[field], str) or not manifest[field].strip():
            raise BuildError(f"{location}.{field} must be a non-empty string")
    expected_repository = f"https://github.com/{slug}"
    if manifest["repository"] != expected_repository:
        raise BuildError(
            f"{location}.repository must equal configured source {expected_repository}"
        )
    manifest_path = _normalize_relative_path(manifest["path"], f"{location}.path")
    if manifest_path != actual_path:
        raise BuildError(
            f"{location}.path {manifest_path!r} does not match discovered path {actual_path!r}"
        )
    try:
        _validate_ref(manifest["ref"], f"{location}.ref")
    except RegistryValidationError as exc:
        raise BuildError(str(exc)) from exc


def _build_skill(repository: SourceRepository, slug: str, skill_path: str) -> Dict[str, Any]:
    manifest_relative = _join_posix(skill_path, "shuku.json")
    skill_relative = _join_posix(skill_path, "SKILL.md")
    preliminary_manifest = _read_json_text(
        repository.read_worktree(manifest_relative), f"{slug}:{manifest_relative}"
    )
    ref = preliminary_manifest.get("ref")
    if not isinstance(ref, str) or not ref.strip():
        raise BuildError(f"{slug}:{manifest_relative}.ref must be a non-empty string")
    try:
        _validate_ref(ref, f"{slug}:{manifest_relative}.ref")
    except RegistryValidationError as exc:
        raise BuildError(str(exc)) from exc

    manifest = _read_json_text(
        repository.read_at_ref(ref, manifest_relative), f"{slug}@{ref}:{manifest_relative}"
    )
    _validate_manifest(manifest, slug, skill_path, f"{slug}@{ref}:{manifest_relative}")
    frontmatter = _parse_frontmatter(
        repository.read_at_ref(ref, skill_relative), f"{slug}@{ref}:{skill_relative}"
    )
    if frontmatter["name"] != manifest["name"]:
        raise BuildError(
            f"{slug}@{ref}:{skill_path} SKILL.md name {frontmatter['name']!r} "
            f"does not match shuku.json name {manifest['name']!r}"
        )

    return {
        "name": frontmatter["name"],
        "description": frontmatter["description"],
        "version": manifest["version"],
        "source": {
            "type": "github",
            "repository": manifest["repository"],
            "ref": manifest["ref"],
            "path": manifest["path"],
        },
        "entrypoint": "SKILL.md",
        "manifest": "shuku.json",
    }


def build_registry(
    sources_path: Path, source_root: Optional[Path] = None
) -> Dict[str, Any]:
    """Resolve configured sources, validate metadata, and return the V1 registry."""

    sources = _load_sources(Path(sources_path))
    skills = []
    names = set()
    with tempfile.TemporaryDirectory(prefix="shuku-registry-") as temp_dir:
        clone_root = Path(temp_dir)
        for source in sources:
            repository = _materialize_repository(
                source["repository"], source_root, clone_root
            )
            for skill_path in _discover_skill_paths(repository, source):
                skill = _build_skill(repository, source["repository"], skill_path)
                if skill["name"] in names:
                    raise BuildError(f"Duplicate skill name: {skill['name']}")
                names.add(skill["name"])
                skills.append(skill)

    registry = {
        "schema_version": 1,
        "provider": "reduct-shuku",
        "skills": sorted(skills, key=lambda skill: skill["name"]),
    }
    try:
        validate_registry(registry)
    except RegistryValidationError as exc:
        raise BuildError(f"Generated registry is invalid: {exc}") from exc
    return registry


def render_registry(registry: Dict[str, Any]) -> str:
    return json.dumps(registry, ensure_ascii=False, indent=2) + "\n"


def write_or_check_registry(registry: Dict[str, Any], output: Path, check: bool) -> None:
    output = Path(output)
    expected = render_registry(registry)
    if check:
        try:
            actual = output.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise BuildError(f"Generated registry is missing: {output}") from exc
        if actual != expected:
            raise BuildError(
                f"Generated registry is out of date: {output}; run build_agent_skills.py"
            )
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as output_file:
        output_file.write(expected)


def main(argv=None) -> int:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sources",
        type=Path,
        default=project_root / "registry" / "sources.json",
        help="Source repository configuration",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=project_root / "registry" / "agent-skills.json",
        help="Generated registry path",
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        help="Use local repository directories below this path instead of cloning GitHub",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Compare generated content with --output without modifying it",
    )
    args = parser.parse_args(argv)

    try:
        registry = build_registry(args.sources, source_root=args.source_root)
        write_or_check_registry(registry, args.output, check=args.check)
    except (BuildError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    action = "Validated" if args.check else "Wrote"
    print(f"{action} {len(registry['skills'])} skills at {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
