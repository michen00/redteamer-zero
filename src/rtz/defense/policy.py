"""Policy data structures and evaluation engine for defense stages."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class PolicyRule:
    """Declarative policy rule containing condition and action payload."""

    rule: str
    if_: dict[str, Any]
    then: dict[str, Any]


@dataclass
class Policy:
    """Collection of policy rules separated by evaluation stage."""

    version: int
    name: str
    pre_input: list[PolicyRule]
    post_output: list[PolicyRule]
    tool_call: list[PolicyRule]


@dataclass
class PolicyAction:
    """Normalized action emitted by policy evaluation."""

    action: Literal["block", "allow", "transform", "escalate"]
    reason: str | None = None
    transform: str | None = None


class PolicyEngine:
    """Evaluate YAML-based defense policies across different stages."""

    def __init__(self, policy: Policy) -> None:
        """Store the compiled policy.

        Args:
            policy: Policy configuration evaluated during flow execution.
        """
        self.policy = policy

    def evaluate_pre_input(self, prompt: str) -> PolicyAction:
        """Evaluate pre-input rules against ``prompt``.

        Args:
            prompt: User-provided text submitted to the system.

        Returns:
            Policy action describing how to handle the prompt.
        """
        for rule in self.policy.pre_input:
            if self._matches_rule(
                rule.if_,
                prompt,
            ):
                return PolicyAction(
                    action=rule.then["action"],
                    reason=rule.then.get("reason"),
                    transform=rule.then.get("transform"),
                )
        return PolicyAction(action="allow")

    def evaluate_tool_call(
        self,
        tool_name: str,
        tool_args: dict[str, Any],
    ) -> PolicyAction:
        """Evaluate tool-call rules using ``tool_name`` and ``tool_args``.

        Args:
            tool_name: Name of the tool requested by the model.
            tool_args: Arguments associated with the tool invocation.

        Returns:
            Policy action specifying whether the tool call is
            allowed.
        """
        for rule in self.policy.tool_call:
            payload = {
                "name": tool_name,
                "args": tool_args,
            }
            if self._matches_rule(rule.if_, payload):
                return PolicyAction(
                    action=rule.then["action"],
                    reason=rule.then.get("reason"),
                    transform=rule.then.get("transform"),
                )
        return PolicyAction(action="allow")

    def evaluate_post_output(self, output: str) -> PolicyAction:
        """Evaluate post-output rules against ``output``.

        Args:
            output: Model response subject to defensive review.

        Returns:
            Policy action describing follow-up handling of the output.
        """
        for rule in self.policy.post_output:
            if self._matches_rule(rule.if_, output):
                return PolicyAction(
                    action=rule.then["action"],
                    reason=rule.then.get("reason"),
                    transform=rule.then.get("transform"),
                )
        return PolicyAction(action="allow")

    def _matches_rule(
        self,
        condition: dict[str, Any],
        target: str | dict[str, Any],
    ) -> bool:
        """Return whether ``condition`` matches ``target``.

        Args:
            condition: Condition map from the policy definition.
            target: Value tested against the condition.

        Returns:
            Boolean indicating if the rule should fire.
        """
        if "regex" in condition:
            patterns = condition["regex"]
            if isinstance(patterns, str):
                patterns = [patterns]
            target_text = target["name"] if isinstance(target, dict) else target
            for pattern in patterns:
                if re.search(pattern, str(target_text), re.IGNORECASE):
                    return True

        if "tool_name_in" in condition:
            tool_names = condition["tool_name_in"]
            if isinstance(tool_names, str):
                tool_names = [tool_names]
            if isinstance(target, dict):
                candidate = str(target.get("name"))
            else:
                candidate = str(target)
            if candidate in tool_names:
                return True

        if "arg_regex" in condition and isinstance(target, dict):
            arg_patterns = condition["arg_regex"]
            if isinstance(arg_patterns, str):
                arg_patterns = [arg_patterns]
            serialized_args = json.dumps(target.get("args", {}), sort_keys=True)
            for pattern in arg_patterns:
                if re.search(pattern, serialized_args, re.IGNORECASE):
                    return True

        return False
