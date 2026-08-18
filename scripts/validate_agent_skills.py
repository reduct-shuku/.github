#!/usr/bin/env python3
"""Validate a generated Shuku agent skills registry."""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List


GITHUB_REPOSITORY_URL = re.compile(
    r"^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$"
)
SAFE_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")


class RegistryValidationError(ValueError):
    """Raised when a generated registry violates its public contract."""


def _require_mapping(value: Any, location: str) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise RegistryValidationError(f"{location} must be a JSON object")
    return value


def _require_exact_keys(
    value: Dict[str, Any], required: Iterable[str], location: str
) -> None:
    required_set = set(required)
    actual_set = set(value)
    if actual_set != required_set:
        missing = sorted(required_set - actual_set)
        extra = sorted(actual_set - required_set)
        details = []
        if missing:
            details.append(f"missing {missing}")
        if extra:
            details.append(f"unexpected {extra}")
        raise RegistryValidationError(f"{location} has invalid fields: {', '.join(details)}")


def _require_nonempty_string(value: Any, location: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RegistryValidationError(f"{location} must be a non-empty string")
    return value


def _validate_relative_path(value: Any, location: str) -> str:
    path = _require_nonempty_string(value, location)
    if "\\" in path or path.startswith("/"):
        raise RegistryValidationError(f"{location} must be a relative POSIX path")
    parts = path.split("/")
    if path != "." and any(part in ("", ".", "..") for part in parts):
        raise RegistryValidationError(f"{location} must not contain empty, '.' or '..' segments")
    return path


def _validate_ref(value: Any, location: str) -> str:
    ref = _require_nonempty_string(value, location)
    if (
        not SAFE_REF.fullmatch(ref)
        or ".." in ref
        or "@{" in ref
        or ref.endswith((".", "/"))
        or "/." in ref
    ):
        raise RegistryValidationError(f"{location} is not a safe Git ref")
    return ref


def validate_registry(registry: Any) -> None:
    """Validate the complete V1 registry schema and deterministic ordering."""

    root = _require_mapping(registry, "registry")
    _require_exact_keys(root, ("schema_version", "provider", "skills"), "registry")
    if root["schema_version"] != 1:
        raise RegistryValidationError("registry.schema_version must equal 1")
    if root["provider"] != "reduct-shuku":
        raise RegistryValidationError("registry.provider must equal 'reduct-shuku'")
    if not isinstance(root["skills"], list):
        raise RegistryValidationError("registry.skills must be a JSON array")

    names: List[str] = []
    for index, raw_skill in enumerate(root["skills"]):
        location = f"registry.skills[{index}]"
        skill = _require_mapping(raw_skill, location)
        _require_exact_keys(
            skill,
            ("name", "description", "version", "source", "entrypoint", "manifest"),
            location,
        )
        name = _require_nonempty_string(skill["name"], f"{location}.name")
        names.append(name)
        _require_nonempty_string(skill["description"], f"{location}.description")
        _require_nonempty_string(skill["version"], f"{location}.version")

        source = _require_mapping(skill["source"], f"{location}.source")
        _require_exact_keys(
            source, ("type", "repository", "ref", "path"), f"{location}.source"
        )
        if source["type"] != "github":
            raise RegistryValidationError(f"{location}.source.type must equal 'github'")
        repository = _require_nonempty_string(
            source["repository"], f"{location}.source.repository"
        )
        if not GITHUB_REPOSITORY_URL.fullmatch(repository):
            raise RegistryValidationError(
                f"{location}.source.repository must be a canonical GitHub repository URL"
            )
        _validate_ref(source["ref"], f"{location}.source.ref")
        _validate_relative_path(source["path"], f"{location}.source.path")

        if skill["entrypoint"] != "SKILL.md":
            raise RegistryValidationError(f"{location}.entrypoint must equal 'SKILL.md'")
        if skill["manifest"] != "shuku.json":
            raise RegistryValidationError(f"{location}.manifest must equal 'shuku.json'")

    if len(names) != len(set(names)):
        duplicates = sorted({name for name in names if names.count(name) > 1})
        raise RegistryValidationError(f"Duplicate skill name(s): {', '.join(duplicates)}")
    if names != sorted(names):
        raise RegistryValidationError("registry.skills must be sorted by skill name")


def load_and_validate(path: Path) -> Dict[str, Any]:
    try:
        registry = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RegistryValidationError(f"Registry file does not exist: {path}") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RegistryValidationError(f"Cannot read registry file {path}: {exc}") from exc
    validate_registry(registry)
    return registry


def main(argv=None) -> int:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=project_root / "registry" / "agent-skills.json",
        help="Registry JSON to validate",
    )
    args = parser.parse_args(argv)
    try:
        registry = load_and_validate(args.path)
    except RegistryValidationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Validated {len(registry['skills'])} skills in {args.path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
