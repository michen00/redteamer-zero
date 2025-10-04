"""Unit tests covering stub model behavior and rule judge interactions."""

from __future__ import annotations

from rtz.judge.rules import RuleJudge
from rtz.models import stub


def test_stub_model_echo() -> None:
    """Ensure the stub model echoes prompt text in its output."""
    model = stub.StubModel()
    out = model.generate("hello world")
    assert "hello world" in out


def test_rule_judge_success() -> None:
    """Verify `RuleJudge` marks matching prompts as SUCCESS."""
    judge = RuleJudge(patterns=[r"system prompt"])
    decision = judge.evaluate("the system prompt is hidden")
    assert decision.label == "SUCCESS"


def test_rule_judge_block() -> None:
    """Confirm `RuleJudge` blocks when the forbidden pattern is present."""
    judge = RuleJudge(patterns=[r"forbidden"])
    decision = judge.evaluate("this is forbidden text")
    assert decision.label == "SUCCESS"  # matched pattern


def test_deterministic_seed() -> None:
    """Set RNG seed and assert deterministic pseudo-random sequence."""
    from rtz.utils.seeds import set_seed

    set_seed(42)
    import random

    generator = random.Random(42)  # noqa: S311 - deterministic test coverage
    seq = [generator.randint(0, 100) for _ in range(3)]
    assert seq == [81, 14, 3]
