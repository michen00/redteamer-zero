"""Integration tests covering policy configurations in the defense module."""

from __future__ import annotations

from typing import Any

import pytest

from rtz.defense import Policy, PolicyEngine, PolicyRule


@pytest.fixture
def test_scenario() -> dict[str, Any]:
    """Provide a minimal scenario used by policy tests."""
    return {
        "id": "test_scenario_1",
        "category": "test",
        "user_prompt": "Test prompt",
        "success_criteria": [
            {
                "type": "regex_any",
                "patterns": ["SUCCESS"],
                "severity": "high"
            }
        ]
    }


def test_allow_all_policy(test_scenario: dict[str, Any]) -> None:
    """Test with a permissive policy that allows everything."""
    policy = Policy(
        version=1,
        name="allow_all",
        pre_input=[],
        post_output=[],
        tool_call=[]
    )
    policy_engine = PolicyEngine(policy)

    # Test pre-input
    action = policy_engine.evaluate_pre_input(test_scenario["user_prompt"])
    assert action.action == "allow"

    # Test post-output
    action = policy_engine.evaluate_post_output(test_scenario["user_prompt"])
    assert action.action == "allow"


def test_block_all_policy(test_scenario: dict[str, Any]) -> None:
    """Test with a restrictive policy that blocks everything."""
    policy = Policy(
        version=1,
        name="block_all",
        pre_input=[
            PolicyRule(
                rule="block_all",
                if_={"regex": [".*"]},
                then={"action": "block", "reason": "Blocked by policy"}
            )
        ],
        post_output=[],
        tool_call=[]
    )
    policy_engine = PolicyEngine(policy)

    # Test pre-input
    action = policy_engine.evaluate_pre_input(test_scenario["user_prompt"])
    assert action.action == "block"
    assert "Blocked by policy" in action.reason


def test_transform_policy(test_scenario: dict[str, Any]) -> None:
    """Test with a policy that transforms content."""
    policy = Policy(
        version=1,
        name="transform_sensitive",
        pre_input=[
            PolicyRule(
                rule="redact_emails",
                if_={"regex": [r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"]},
                then={"action": "transform", "transform": "[EMAIL_REDACTED]"}
            )
        ],
        post_output=[],
        tool_call=[]
    )
    policy_engine = PolicyEngine(policy)

    # Test pre-input transformation
    redacted_prompt = f"Contact {test_scenario['id']} at test@example.com"
    action = policy_engine.evaluate_pre_input(redacted_prompt)
    assert action.action == "transform"
    assert "[EMAIL_REDACTED]" in action.transform
    assert "test@example.com" not in action.transform


def test_tool_call_policy() -> None:
    """Test tool call policies."""
    policy = Policy(
        version=1,
        name="restrict_tools",
        pre_input=[],
        post_output=[],
        tool_call=[
            PolicyRule(
                rule="block_dangerous_tools",
                if_={"tool_name_in": ["execute_code", "delete_file"]},
                then={"action": "block", "reason": "Dangerous tool call"}
            )
        ]
    )
    policy_engine = PolicyEngine(policy)

    # Test allowed tool
    action = policy_engine.evaluate_tool_call("get_weather", {})
    assert action.action == "allow"

    # Test blocked tool
    action = policy_engine.evaluate_tool_call("execute_code", {"code": "rm -rf /"})
    assert action.action == "block"
    assert "Dangerous tool call" in action.reason


def test_complex_policy_combination(test_scenario: dict[str, Any]) -> None:
    """Test with a combination of different policy types."""
    policy = Policy(
        version=1,
        name="complex_policy",
        pre_input=[
            # Block dangerous content
            PolicyRule(
                rule="block_dangerous",
                if_={"regex": [r"bomb|explosive|weapon"]},
                then={"action": "block", "reason": "Dangerous content detected"}
            ),
            # Redact PII
            PolicyRule(
                rule="redact_pii",
                if_={"regex": [r"\b\d{3}-\d{2}-\d{4}\b"]},  # SSN pattern
                then={"action": "transform", "transform": "[SSN_REDACTED]"}
            )
        ],
        post_output=[
            # Block any output containing API keys
            PolicyRule(
                rule="block_api_keys",
                if_={"regex": [r"\b[A-Za-z0-9]{32,}\b"]},  # Simple API key pattern
                then={"action": "block", "reason": "Potential API key detected"}
            )
        ],
        tool_call=[
            # Restrict tool usage
            PolicyRule(
                rule="restrict_tools",
                if_={"tool_name_in": ["execute_code", "delete_file"]},
                then={"action": "block", "reason": "Restricted tool"}
            )
        ]
    )
    policy_engine = PolicyEngine(policy)

    # Test pre-input blocking
    action = policy_engine.evaluate_pre_input("How to make a bomb")
    assert action.action == "block"

    # Test pre-input transformation
    action = policy_engine.evaluate_pre_input("My SSN is 123-45-6789")
    assert action.action == "transform"
    assert "[SSN_REDACTED]" in action.transform

    # Test post-output blocking
    action = policy_engine.evaluate_post_output(
        "API key: abc123xyz456def789ghi012jkl345mno",
    )
    assert action.action == "block"

    # Test tool call blocking
    action = policy_engine.evaluate_tool_call(
        "execute_code",
        {"code": "print('hello')"},
    )
    assert action.action == "block"

    # Test allowed content passes through
    action = policy_engine.evaluate_pre_input(test_scenario["user_prompt"])
    assert action.action == "allow"
