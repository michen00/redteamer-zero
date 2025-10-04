"""Adapters for loading defense policies from YAML and in-memory data."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .policy import Policy, PolicyRule


def load_policy_from_yaml(file_path: str | Path) -> Policy:
    """Load a policy definition from a YAML file.

    Args:
        file_path: Location of the YAML policy file.

    Returns:
        Parsed `Policy` instance.
    """
    path = Path(file_path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    return Policy(
        version=data["version"],
        name=data["name"],
        pre_input=[PolicyRule(**rule) for rule in data.get("pre_input", [])],
        post_output=[PolicyRule(**rule) for rule in data.get("post_output", [])],
        tool_call=[PolicyRule(**rule) for rule in data.get("tool_call", [])],
    )


def load_policy_from_dict(data: dict[str, Any]) -> Policy:
    """Load a policy definition from an in-memory mapping.

    Args:
        data: Dictionary matching the policy schema.

    Returns:
        Parsed `Policy` instance.
    """
    return Policy(
        version=data["version"],
        name=data["name"],
        pre_input=[PolicyRule(**rule) for rule in data.get("pre_input", [])],
        post_output=[PolicyRule(**rule) for rule in data.get("post_output", [])],
        tool_call=[PolicyRule(**rule) for rule in data.get("tool_call", [])],
    )
