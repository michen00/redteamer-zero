"""Integration test verifying the full RTZ pipeline end-to-end."""

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING

from rtz.defense import Policy, PolicyEngine, PolicyRule
from rtz.judge import RuleJudge
from rtz.models.stub import StubModel
from rtz.orchestration.langgraph_flow import RTZState, build_graph

if TYPE_CHECKING:
    from pathlib import Path


def test_full_pipeline(tmp_path: Path) -> None:
    """Test the complete pipeline from scenario to report."""
    # Create test scenario file
    scenario = {
        "id": "test_scenario_1",
        "category": "test",
        "user_prompt": "Test prompt",
        "success_criteria": [
            {"type": "regex_any", "patterns": ["SUCCESS"], "severity": "high"}
        ],
    }

    scenario_file = tmp_path / "test_scenario.yaml"
    scenario_file.write_text(
        dedent(
            """
            ---
            id: test_scenario_1
            category: test
            user_prompt: Test prompt
            success_criteria:
              - type: regex_any
                patterns: [SUCCESS]
                severity: high
            """
        ).strip(),
    )

    # Create test policy
    policy = Policy(
        version=1,
        name="test_policy",
        pre_input=[
            PolicyRule(
                rule="block_dangerous",
                if_={"regex": ["dangerous", "explosive"]},
                then={"action": "block", "reason": "Dangerous content"},
            )
        ],
        post_output=[],
        tool_call=[],
    )

    # Create test model that responds with SUCCESS on second attempt
    class TestModel(StubModel):
        """Stub model which succeeds on the second invocation."""

        def __init__(self) -> None:
            """Initialize call counter."""
            self.call_count = 0

        def generate(self, _prompt: str) -> str:
            """Return non-success first, then ``SUCCESS`` on subsequent calls."""
            self.call_count += 1
            if self.call_count == 1:
                return "First attempt"
            return "SUCCESS"  # Will pass on second attempt

    # Build and run the graph
    model = TestModel()
    policy_engine = PolicyEngine(policy)
    judge = RuleJudge(patterns=["SUCCESS"])

    graph = build_graph(model=model, policy_engine=policy_engine, judge=judge)

    # Initial state
    initial_state: RTZState = {
        "seed": 42,
        "budget_usd": 1.0,
        "scenario": scenario,
        "attempt": 0,
        "attack_prompt": None,
        "defense_actions": [],
        "model_output": None,
        "judgement": None,
        "learner_state": {},
        "costs": {},
        "done": False,
    }

    # Run the graph (should take 2 attempts)
    state = initial_state
    for _ in range(3):  # Max 3 steps
        state = graph.invoke(state)
        if state.get("done"):
            break

    # Verify results
    assert state["done"] is True
    assert "judgement" in state
    assert state["judgement"]["success"] is True
    assert state["attempt"] == 2  # Should succeed on second attempt
    assert state["budget_usd"] < 1.0  # Budget should be reduced

    # Verify report data
    assert "costs" in state
    assert "defense_actions" in state
    assert len(state["defense_actions"]) > 0
