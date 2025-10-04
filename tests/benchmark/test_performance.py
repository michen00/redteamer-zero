"""Performance benchmarks for RedTeamer Zero orchestration flow."""

from __future__ import annotations

import time
from statistics import mean, stdev
from typing import TYPE_CHECKING

from rtz.orchestration.langgraph_flow import RTZState, build_graph

if TYPE_CHECKING:
    from collections.abc import Callable

    from pytest_benchmark.fixture import BenchmarkFixture


def benchmark(func: Callable[[], None], n: int = 10) -> dict[str, float]:
    """Run ``func`` ``n`` times and return simple timing statistics."""
    if not callable(func):
        error_message = "benchmark() requires a callable input"
        raise TypeError(error_message)

    times = []
    for _ in range(n):
        start = time.perf_counter()
        func()
        times.append(time.perf_counter() - start)

    return {
        "min": min(times) * 1000,  # ms
        "max": max(times) * 1000,
        "mean": mean(times) * 1000,
        "stdev": stdev(times) * 1000 if len(times) > 1 else 0,
    }


def create_test_state() -> RTZState:
    """Create a canonical `RTZState` baseline for benchmarks."""
    return {
        "seed": 42,
        "budget_usd": 1.0,
        "scenario": {
            "id": "benchmark",
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
    }


def test_benchmark_flow(benchmark: BenchmarkFixture) -> None:
    """Benchmark the full flow execution using ``pytest``'s fixture."""
    graph = build_graph()
    state = create_test_state()

    def run_flow() -> None:
        """Invoke the flow and sanity-check judgement presence."""
        result = graph.invoke(state.copy())
        assert "judgement" in result

    benchmark.pedantic(run_flow, rounds=100, iterations=1)


def test_benchmark_components() -> None:
    """Benchmark individual LangGraph components in isolation."""
    graph = build_graph()
    state = create_test_state()

    attacker_node = graph.nodes["attacker"]

    def bench_attacker() -> None:
        """Invoke the attacker node using a fresh state copy."""
        attacker_node.invoke(state.copy())

    attacker_stats = benchmark(bench_attacker)
    assert attacker_stats["min"] >= 0

    defender_node = graph.nodes["defender"]

    def bench_defender() -> None:
        """Invoke defender on a prepared state with prompt populated."""
        s = state.copy()
        s["attack_prompt"] = "test"
        defender_node.invoke(s)

    defender_stats = benchmark(bench_defender)
    assert defender_stats["min"] >= 0

    judge_node = graph.nodes["judge"]

    def bench_judge() -> None:
        """Invoke judge node after injecting matching model output."""
        s = state.copy()
        s["model_output"] = "SUCCESS"
        judge_node.invoke(s)

    judge_stats = benchmark(bench_judge)
    assert judge_stats["min"] >= 0

    learner_node = graph.nodes["learner"]

    def bench_learner() -> None:
        """Invoke learner node with failing judgement to force retry."""
        s = state.copy()
        s["judgement"] = {"success": False, "label": "FAIL", "reason": "test"}
        learner_node.invoke(s)

    learner_stats = benchmark(bench_learner)
    assert learner_stats["min"] >= 0


def test_memory_usage() -> None:
    """Test that memory usage doesn't grow with multiple runs."""
    import gc
    import tracemalloc

    graph = build_graph()
    state = create_test_state()

    tracemalloc.start()
    snapshot1 = tracemalloc.take_snapshot()

    for _ in range(100):
        s = state.copy()
        graph.invoke(s)
        del s
        gc.collect()

    snapshot2 = tracemalloc.take_snapshot()
    tracemalloc.stop()

    diff = snapshot2.compare_to(snapshot1, "lineno")
    total_diff = sum(d.size_diff for d in diff)
    assert total_diff < 1024 * 1024  # Less than 1MB growth
