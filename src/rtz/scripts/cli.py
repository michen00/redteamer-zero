"""Command-line interface for the RedTeamer Zero toolkit."""

import argparse
import json
import logging
import sys
from collections.abc import Iterable
from contextlib import suppress
from pathlib import Path

import yaml

from rtz.judge.rules import RuleJudge
from rtz.models.stub import StubModel
from rtz.utils.seeds import set_seed

LOGGER = logging.getLogger(__name__)


def _expand_patterns(patterns: Iterable[str]) -> list[Path]:
    """Expand glob patterns relative to the current directory."""
    matches: set[Path] = set()
    for pattern in patterns:
        path = Path(pattern)
        if path.is_absolute():
            if path.exists():
                matches.add(path)
            else:
                matches.update(path.parent.glob(path.name))
            continue

        for match in Path().glob(pattern):
            matches.add(Path(match))
    return sorted(matches)


def cmd_run(args: argparse.Namespace) -> int:
    """Execute the ``run`` subcommand.

    Args:
        args: Parsed CLI arguments namespace.

    Returns:
        Exit status code.
    """
    set_seed(args.seed)

    # Load scenarios
    scenario_paths = _expand_patterns(args.scenarios)
    scenarios = []
    for scenario_path in scenario_paths:
        with scenario_path.open(encoding="utf-8") as handle:
            document = yaml.safe_load(handle)
        if isinstance(document, list):
            scenarios.extend(document)
        else:
            scenarios.append(document)

    # Load policy (not enforced here; stub)
    _policy = None
    if args.policy:
        policy_path = Path(args.policy)
        with policy_path.open(encoding="utf-8") as handle:
            _policy = yaml.safe_load(handle)

    # Choose model (support stub only for now)
    if args.model.startswith("stub"):
        model = StubModel()
    else:
        message = f"Unknown model adapter: {args.model}"
        raise SystemExit(message)

    # Simple judge: regex_any on scenario success criteria if provided
    out_dir = Path(args.report)
    out_dir.mkdir(parents=True, exist_ok=True)
    trace_path = out_dir / "trace.jsonl"

    from datetime import datetime

    with trace_path.open("w", encoding="utf-8") as trace:
        successful = 0
        failed = 0
        total_cost = 0.0
        for attempt_index, scenario in enumerate(scenarios):
            user_prompt = scenario.get("user_prompt", "")
            model_output = model.generate(user_prompt)

            patterns: list[str] = []
            for criterion in scenario.get("success_criteria", []) or []:
                if criterion.get("type") == "regex_any":
                    patterns.extend(criterion.get("patterns", []))
            judge = RuleJudge(patterns=patterns or [r"system prompt"])
            decision = judge.evaluate(model_output)

            # Minimal metadata and ISO8601 timestamp
            event = {
                "attempt": attempt_index,
                "scenario_id": scenario.get("id"),
                "category": scenario.get("category"),
                "prompt": user_prompt,
                "model": getattr(model, "name", "stub"),
                "output": model_output,
                "decision": {
                    "label": decision.label,
                    "reason": decision.reason,
                    "score": getattr(decision, "score", None),
                },
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "metadata": scenario.get("metadata", {}),
            }
            # Update running summary counters
            if decision.label in {"SUCCESS", "PASS"}:
                successful += 1
            else:
                failed += 1
            # stub model cost approximation
            total_cost += 0.01

            trace.write(json.dumps(event) + "\n")

    # Write minimal summary matching tests
    summary = {
        "total_scenarios": len(scenarios),
        "successful_runs": successful,
        "failed_runs": failed,
        "total_cost": total_cost,
        "trace": str(trace_path),
    }
    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    LOGGER.info("Processed %s scenarios", len(scenarios))
    json.dump(summary, sys.stdout)
    sys.stdout.write("\n")
    return 0


def cmd_tune(_: argparse.Namespace) -> int:
    """Execute the ``tune`` subcommand placeholder.

    Args:
        _: Parsed CLI arguments namespace (unused).

    Returns:
        Exit status code.
    """
    LOGGER.warning("Tune stub (not implemented yet)")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Execute the ``report`` subcommand.

    Args:
        args: Parsed CLI arguments namespace.

    Returns:
        Exit status code.
    """
    # Concatenate multiple traces and emit a placeholder HTML report
    # Accept either --trace or --input for compatibility with tests/examples
    sources = getattr(args, "trace", None) or getattr(args, "input", None) or []
    traces = _expand_patterns(sources)

    records = []
    for trace_path in traces:
        with trace_path.open(encoding="utf-8") as handle:
            for line in handle:
                with suppress(json.JSONDecodeError):
                    records.append(json.loads(line))

    # A tiny HTML page that prints counts
    data_blob = json.dumps(records, indent=2)
    html = (
        "<!doctype html>\n"
        "<html>\n"
        "<head><meta charset='utf-8'><title>RTZ Report</title></head>\n"
        "<body>\n"
        "  <h1>RedTeamer Zero Report</h1>\n"
        f"  <p>Total events: {len(records)}</p>\n"
        '  <pre id="data" style="white-space: pre-wrap">'
        f"{data_blob}</pre>\n"
        "</body>\n"
        "</html>\n"
    )

    out_path = Path(getattr(args, "html", None) or getattr(args, "output", None))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    LOGGER.info("Wrote report to %s", out_path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the CLI.

    Returns:
        Configured argument parser.
    """
    p = argparse.ArgumentParser(prog="rtz", description="RedTeamer Zero CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("run")
    pr.add_argument("--scenarios", nargs="+", required=True)
    pr.add_argument("--policy", required=True)
    pr.add_argument("--model", required=True)
    pr.add_argument("--budget.usd", dest="budget_usd", type=float, default=0.0)
    pr.add_argument("--seed", type=int, default=42)
    pr.add_argument("--report", required=True)
    pr.set_defaults(func=cmd_run)

    pt = sub.add_parser("tune")
    pt.add_argument("--policy", required=True)
    pt.add_argument("--scenarios", nargs="+", required=True)
    pt.set_defaults(func=cmd_tune)

    prep = sub.add_parser("report")
    # Accept both --trace and --input for compatibility with tests/examples
    prep.add_argument("--trace", nargs="+", required=False)
    prep.add_argument("--input", nargs="+", required=False)
    # Accept both --html and --output
    prep.add_argument("--html", required=False)
    prep.add_argument("--output", required=False)
    prep.set_defaults(func=cmd_report)

    return p


def main(argv: list[str] | None = None) -> int:
    """Entry point for the CLI.

    Args:
        argv: Optional list of command-line arguments.

    Returns:
        Exit status code.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        handler = args.func
    except AttributeError as exc:  # pragma: no cover - argparse guarantees attribute
        message = "Parser did not set a handler"
        raise TypeError(message) from exc

    if not callable(handler):
        message = "Parser returned a non-callable handler"
        raise TypeError(message)

    result = handler(args)
    if not isinstance(result, int):
        message = f"Handler returned non-integer exit code: {result!r}"
        raise TypeError(message)

    return result


if __name__ == "__main__":
    raise SystemExit(main())
