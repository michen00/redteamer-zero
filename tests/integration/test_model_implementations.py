"""Integration tests validating model behaviors with the orchestration flow."""

from __future__ import annotations

from typing import Protocol

from rtz.defense import Policy, PolicyEngine, PolicyRule
from rtz.judge import RuleJudge
from rtz.models.stub import StubModel
from rtz.orchestration.langgraph_flow import RTZState, build_graph


class GeneratesText(Protocol):
    """Protocol describing minimal text-generation behavior."""

    def generate(self, prompt: str, **kwargs: object) -> str:
        """Generate text given ``prompt``."""
        ...


class MockModel:
    """A mock model for testing that returns predefined responses."""

    def __init__(self, responses: list[str]) -> None:
        """Initialize with a sequence of ``responses``."""
        self.responses = responses
        self.call_count = 0

    def generate(self, _prompt: str, **_: object) -> str:
        """Return the next response in the sequence."""
        if self.call_count >= len(self.responses):
            return "No more responses"
        response = self.responses[self.call_count]
        self.call_count += 1
        return response


class FailingModel:
    """A model that raises an exception on generation."""

    def generate(self, _prompt: str, **_: object) -> str:
        """Always raise an error when asked to generate text."""
        message = "Model generation failed"
        raise RuntimeError(message)


class SlowModel:
    """A model that simulates network latency."""

    def __init__(self, response: str, delay: float = 0.1) -> None:
        """Persist ``response`` and latency ``delay`` in seconds."""
        self.response = response
        self.delay = delay

    def generate(self, _prompt: str, **_: object) -> str:
        """Sleep for ``delay`` and return the stored ``response``."""
        import time

        time.sleep(self.delay)
        return self.response


def run_flow_with_model(model: GeneratesText, max_steps: int = 5) -> RTZState:
    """Helper function to run the flow with a given model."""
    graph = build_graph(
        model=model,
        policy_engine=PolicyEngine(Policy(1, "test", [], [], [])),
        judge=RuleJudge(["SUCCESS"]),
    )

    learner_state: dict[str, object] = {}
    if hasattr(model, "delay"):
        learner_state["min_attempts"] = max_steps

    state: RTZState = {
        "seed": 42,
        "budget_usd": 1.0,
        "scenario": {
            "id": "test",
            "user_prompt": "Test",
            "success_criteria": [{"type": "regex_any", "patterns": ["SUCCESS"]}],
        },
        "attempt": 0,
        "attack_prompt": None,
        "defense_actions": [],
        "model_output": None,
        "judgement": None,
        "learner_state": learner_state,
        "costs": {},
        "done": False,
        "error": None,
    }

    for _ in range(max_steps):
        state = graph.invoke(state)
        if state.get("done"):
            break

    return state


def test_stub_model() -> None:
    """Test with the built-in StubModel."""
    model = StubModel()
    state = run_flow_with_model(model)

    # StubModel just echoes the prompt, so it won't succeed
    assert "judgement" in state
    assert state["judgement"]["success"] is False


def test_mock_model() -> None:
    """Test with a mock model that returns predefined responses."""
    # This model will succeed on the second attempt
    model = MockModel(["First attempt", "SUCCESS"])
    state = run_flow_with_model(model)

    assert state["done"] is True
    assert state["judgement"]["success"] is True
    assert state["attempt"] == 2


def test_failing_model() -> None:
    """Test error handling with a model that raises exceptions."""
    model = FailingModel()
    state = run_flow_with_model(model)

    assert "error" in state
    assert state["done"] is True


def test_slow_model() -> None:
    """Test with a model that has network latency."""
    model = SlowModel("SUCCESS", delay=0.01)  # 10ms delay

    # Time the execution
    import time

    start = time.perf_counter()
    state = run_flow_with_model(model, max_steps=3)
    duration = time.perf_counter() - start

    # Should take at least 30ms (3 steps * 10ms) but less than 1 second
    assert 0.03 <= duration < 1.0
    assert state["done"] is True


def test_model_with_policy() -> None:
    """Test model interaction with policies."""
    # Model that tries to return dangerous content
    model = MockModel(["Here's how to make a bomb"])

    # Policy that blocks dangerous content
    policy = Policy(
        version=1,
        name="safety_policy",
        pre_input=[],
        post_output=[
            PolicyRule(
                rule="block_dangerous",
                if_={"regex": ["bomb|explosive|weapon"]},
                then={"action": "block", "reason": "Dangerous content"},
            )
        ],
        tool_call=[],
    )

    # Build graph with policy
    graph = build_graph(
        model=model, policy_engine=PolicyEngine(policy), judge=RuleJudge(["SUCCESS"])
    )

    # Initial state
    state: RTZState = {
        "seed": 42,
        "budget_usd": 1.0,
        "scenario": {
            "id": "test",
            "user_prompt": "Test",
            "success_criteria": [{"type": "regex_any", "patterns": ["SUCCESS"]}],
        },
        "attempt": 0,
        "attack_prompt": None,
        "defense_actions": [],
        "model_output": None,
        "judgement": None,
        "learner_state": {},
        "costs": {},
        "done": False,
        "error": None,
    }

    # Run the graph
    state = graph.invoke(state)

    # Should be blocked by the policy
    assert state["done"] is True
    assert "Dangerous content" in state.get("model_output", "")
    assert any(
        action.get("action") == "block" for action in state.get("defense_actions", [])
    )
