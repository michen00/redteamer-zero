"""Tests covering CLI workflows and rule-based judging behavior.

This module contains tests for the command-line interface and input/output operations
of the RedTeamer Zero tool. It verifies that the CLI commands work as expected and
that the output files are generated correctly.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from rtz.judge.rules import RuleJudge
from rtz.scripts.cli import main as rtz_main


@pytest.mark.parametrize(
    ("patterns", "input_text", "expected_label", "expected_score"),
    (
        # No pattern matches
        ([r"nope"], "the system prompt is hidden", "FAIL", 1.0),
        # Exact match
        ([r"hidden"], "the system prompt is hidden", "PASS", 0.0),
        # Case insensitive match
        ([r"SYSTEM"], "the system prompt is hidden", "PASS", 0.0),
        # Multiple patterns (AND logic)
        ([r"system", r"hidden"], "the system prompt is hidden", "PASS", 0.0),
        # Multiple patterns with one not matching
        ([r"system", r"visible"], "the system prompt is hidden", "FAIL", 1.0),
    ),
)
def test_rule_judge(
    patterns: list[str], input_text: str, expected_label: str, expected_score: float
) -> None:
    """Test RuleJudge with various patterns and inputs.

    Args:
        patterns: List of regex patterns to match against the input text.
        input_text: The text to evaluate.
        expected_label: Expected label from the judge.
        expected_score: Expected score from the judge.
    """
    judge = RuleJudge(patterns=patterns, case_sensitive=False)
    decision = judge.evaluate(input_text)
    assert decision.label == expected_label
    assert decision.score == expected_score


@pytest.mark.parametrize(
    ("model", "budget", "expected_scenario_count"),
    (
        ("stub:echo", "0.05", 3),  # Basic test with echo model
        ("stub:echo", "0.01", 1),  # Lower budget, expect fewer scenarios
    ),
)
def test_cli_run_creates_trace_and_summary(
    tmp_path: Path, model: str, budget: str, expected_scenario_count: int
) -> None:
    """Verify the CLI `run` command writes trace and summary artifacts.

    Args:
        tmp_path: Pytest fixture for temporary directory.
        model: The model to use for testing.
        budget: Budget for the test run.
        expected_scenario_count: Expected number of scenarios to run.
    """
    repo_root = Path(__file__).resolve().parents[1]
    scenarios_glob = str(repo_root / "scenarios" / "basic" / "*.yaml")
    policy_path = str(repo_root / "policies" / "baseline.yaml")
    out_dir = tmp_path / "run"

    code = rtz_main(
        [
            "run",
            "--scenarios",
            scenarios_glob,
            "--policy",
            policy_path,
            "--model",
            model,
            "--budget.usd",
            budget,
            "--seed",
            "123",
            "--report",
            str(out_dir),
        ]
    )
    assert code == 0

    trace_path = out_dir / "trace.jsonl"
    summary_path = out_dir / "summary.json"
    assert trace_path.exists()
    assert summary_path.exists()

    # Verify trace file content
    lines = trace_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= expected_scenario_count

    # Check first entry structure
    first = json.loads(lines[0])
    expected_keys = {
        "attempt",
        "scenario_id",
        "prompt",
        "output",
        "timestamp",
        "metadata",
    }

    # Verify all expected keys are present
    missing_keys = expected_keys - first.keys()
    assert not missing_keys, f"Missing expected keys: {missing_keys}"

    # Verify timestamp format (ISO 8601)
    if "timestamp" in first:
        assert re.match(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})?$",
            first["timestamp"],
        ), "Timestamp is not in ISO 8601 format"

    # Verify summary file content
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert "total_scenarios" in summary
    assert "successful_runs" in summary
    assert "failed_runs" in summary
    assert "total_cost" in summary

    # Verify budget was respected
    if "total_cost" in summary and summary["total_cost"] > 0:
        assert float(budget) >= summary["total_cost"], "Budget exceeded"


@pytest.mark.parametrize(
    ("input_file", "expected_output"),
    (
        ("trace.jsonl", "report.html"),  # Default output filename
        ("trace.jsonl", "custom.html"),  # Custom output filename
    ),
)
def test_cli_report_outputs_html(
    tmp_path: Path, input_file: str, expected_output: str
) -> None:
    """Test HTML report generation with different configurations.

    Args:
        tmp_path: Pytest fixture for temporary directory.
        input_file: Input trace file name.
        expected_output: Expected output HTML file name.
    """
    repo_root = Path(__file__).resolve().parents[1]
    example_trace = repo_root / "examples" / input_file
    out_dir = tmp_path / "report"
    out_dir.mkdir()

    # Generate report with custom output filename
    output_path = out_dir / expected_output
    code = rtz_main(
        [
            "report",
            "--input",
            str(example_trace),
            "--output",
            str(output_path),
        ]
    )

    assert code == 0
    assert output_path.exists()

    # Verify HTML content
    content = output_path.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content
    assert "<title>RedTeamer Zero Report</title>" in content
