"""Workflow assembly utilities built on LangGraph for RedTeamer Zero."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, TypedDict

try:  # Preferred on py3.11+, fallback to typing_extensions for older Pythons
    from typing import NotRequired
except ImportError:  # pragma: no cover - environment dependent
    from typing_extensions import NotRequired  # noqa: TC002

from langgraph.graph import END, StateGraph

from rtz.defense import Policy, PolicyEngine
from rtz.judge import RuleJudge
from rtz.models.stub import StubModel
from rtz.utils.logging import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable

    from langgraph.pregel import Pregel


logger = get_logger(__name__)


class SupportsGenerate(Protocol):
    """Protocol describing the attacker model interface."""

    def generate(self, prompt: str, **kwargs: object) -> str:
        """Return a generated attack string for ``prompt``."""


class RTZState(TypedDict):
    """Mutable state passed between LangGraph nodes."""

    seed: int
    budget_usd: float
    scenario: dict[str, Any]
    attempt: int
    attack_prompt: str | None
    defense_actions: list[dict[str, Any]]
    model_output: str | None
    learner_state: dict[str, Any]
    costs: dict[str, float]
    done: bool
    judgement: NotRequired[dict[str, Any] | None]
    error: NotRequired[str | None]


def create_attacker_node(model: SupportsGenerate) -> Callable[[RTZState], RTZState]:
    """Construct a node that produces attack prompts using ``model``.

    Args:
        model: Model-like object capable of generating attack prompts.

    Returns:
        Callable that mutates the graph state with a generated attack prompt.
    """

    def attacker_node(state: RTZState) -> RTZState:
        """Generate an attack prompt for the current attempt."""
        logger.info(
            "attacker-generating-prompt",
            attempt=state["attempt"],
            budget_usd=state["budget_usd"],
        )
        seed_prompt = (
            f"{state['scenario']['user_prompt']} "
            f"[Attempt {state['attempt']}, Budget: ${state['budget_usd']:.2f}]"
        )
        try:
            attack_prompt = model.generate(seed_prompt)
        except Exception as exc:
            logger.exception("attacker_generation_failed", exc_info=exc)
            return {
                **state,
                "attack_prompt": None,
                "model_output": None,
                "error": f"Attacker failed: {exc}",
                "done": True,
                "costs": {
                    **state.get("costs", {}),
                    "attack_generation": 0.0,
                },
            }

        decorated_prompt = (
            f"{attack_prompt} (attempt {state['attempt']}, "
            f"Budget ${state['budget_usd']:.2f})"
        )

        return {
            **state,
            "attack_prompt": decorated_prompt,
            "costs": {
                **state.get("costs", {}),
                "attack_generation": 0.01,
            },
            "error": None,
        }

    return attacker_node


def create_defender_node(policy_engine: PolicyEngine) -> Callable[[RTZState], RTZState]:
    """Construct a node that applies defensive policy checks.

    Args:
        policy_engine: Instance used to evaluate pre- and post-output rules.

    Returns:
        Callable that enriches state with defense outcomes or blocks execution.
    """

    def defender_node(state: RTZState) -> RTZState:
        """Evaluate policy stages and optionally block the attack."""
        if state.get("error"):
            return state

        attack_prompt = state.get("attack_prompt")
        if attack_prompt is None:
            return {**state, "done": True, "error": "No attack prompt provided"}

        actions: list[dict[str, Any]] = []

        pre_action = policy_engine.evaluate_pre_input(attack_prompt)
        pre_record: dict[str, Any] = {"stage": "pre_input", "action": pre_action.action}
        if pre_action.reason:
            pre_record["reason"] = pre_action.reason
        if pre_action.transform:
            pre_record["transform"] = pre_action.transform

        if pre_action.action == "block":
            logger.info("defense blocked prompt", reason=pre_action.reason)
            return {
                **state,
                "defense_actions": [pre_record],
                "model_output": f"Blocked by defense: {pre_action.reason}",
                "done": True,
            }

        if pre_action.action == "escalate":
            logger.info("defense escalated prompt", reason=pre_action.reason)
            return {
                **state,
                "defense_actions": [pre_record],
                "model_output": f"Escalated by defense: {pre_action.reason}",
                "done": True,
            }

        working_prompt = pre_action.transform or attack_prompt
        actions.append(pre_record)

        model_output = f"Simulated response to: {working_prompt}"

        post_action = policy_engine.evaluate_post_output(model_output)
        post_record: dict[str, Any] = {
            "stage": "post_output",
            "action": post_action.action,
        }
        if post_action.reason:
            post_record["reason"] = post_action.reason
        if post_action.transform:
            post_record["transform"] = post_action.transform

        if post_action.action == "block":
            logger.info("defense blocked output", reason=post_action.reason)
            actions.append(post_record)
            return {
                **state,
                "defense_actions": actions,
                "model_output": f"Blocked by defense: {post_action.reason}",
                "done": True,
            }

        if post_action.action == "escalate":
            logger.info("defense escalated output", reason=post_action.reason)
            actions.append(post_record)
            return {
                **state,
                "defense_actions": actions,
                "model_output": f"Escalated by defense: {post_action.reason}",
                "done": True,
            }

        final_output = post_action.transform or model_output
        actions.append(post_record)

        return {
            **state,
            "model_output": final_output,
            "defense_actions": actions,
        }

    return defender_node


def create_judge_node(judge: RuleJudge) -> Callable[[RTZState], RTZState]:
    """Construct a node that scores model responses via ``judge``.

    Args:
        judge: Rule-based judge used to determine success.

    Returns:
        Callable that augments state with judgment metadata.
    """

    def judge_node(state: RTZState) -> RTZState:
        """Evaluate the latest model output and persist the decision."""
        if state.get("error"):
            return state

        if not state.get("model_output"):
            return {**state, "done": True, "error": "No model output to judge"}

        decision = judge.evaluate(state["model_output"])

        # Normalize success for both legacy labels
        judgement = {
            "label": decision.label,
            "reason": decision.reason,
            "success": decision.label in ("SUCCESS", "PASS"),
        }

        return {
            **state,
            "judgement": judgement,
            "error": None,
        }

    return judge_node


def create_learner_node() -> Callable[[RTZState], RTZState]:
    """Construct a learner node that updates strategy state across attempts.

    Returns:
        Callable that updates counters, budget, and loop control fields.
    """

    def learner_node(state: RTZState) -> RTZState:
        """Update learner metadata based on the latest judgement."""
        judgement = state.get("judgement") or {}
        error = state.get("error")
        prev_done = state.get("done", False)

        costs = state.get("costs", {})
        step_cost = costs.get("attack_generation")
        remaining_budget = state["budget_usd"]
        if step_cost is None:
            step_cost = 0.01

        remaining_budget = max(0.0, remaining_budget - step_cost)

        learner_state = dict(state.get("learner_state", {}))
        total_attempts = learner_state.get("total_attempts", 0) + 1
        learner_state["total_attempts"] = total_attempts

        success = judgement.get("success", False)
        success_streak = learner_state.get("success_streak", 0)
        required_success_attempts = max(
            1,
            int(learner_state.get("required_success_attempts", 1)),
        )

        min_attempts = max(1, int(learner_state.get("min_attempts", 1)))

        if success:
            success_streak += 1
        else:
            success_streak = 0

        learner_state["success_streak"] = success_streak
        learner_state["required_success_attempts"] = required_success_attempts
        learner_state["last_attempt_success"] = success
        learner_state["min_attempts"] = min_attempts

        attempt_limit = learner_state.get("attempt_limit")
        if attempt_limit is None:
            attempt_limit = 20
        learner_state["attempt_limit"] = attempt_limit

        next_attempt = state["attempt"] + 1
        success_completed = (
            success_streak >= required_success_attempts
            and total_attempts >= min_attempts
        )

        done = (
            prev_done
            or success_completed
            or bool(error)
            or remaining_budget <= 0.0
            or next_attempt >= attempt_limit
        )

        return {
            **state,
            "budget_usd": remaining_budget,
            "attempt": next_attempt,
            "learner_state": learner_state,
            "done": done,
        }

    return learner_node


def build_graph(
    model: SupportsGenerate | None = None,
    policy_engine: PolicyEngine | None = None,
    judge: RuleJudge | None = None,
) -> Pregel:
    """Build the LangGraph flow that coordinates attacker, defender, and judge.

    Args:
        model: Optional model instance used by the attacker node.
        policy_engine: Policy engine for defensive evaluations.
        judge: Rule-based judge for scoring outputs.

    Returns:
        Compiled LangGraph ``Pregel`` workflow ready for execution.
    """
    if model is None:
        model = StubModel()
    if policy_engine is None:
        policy_engine = PolicyEngine(
            Policy(
                version=1,
                name="default",
                pre_input=[],
                post_output=[],
                tool_call=[],
            ),
        )
    if judge is None:
        judge = RuleJudge(patterns=[r"NEVER_MATCH"])

    workflow = StateGraph(RTZState)

    workflow.add_node("attacker", create_attacker_node(model))
    workflow.add_node("defender", create_defender_node(policy_engine))
    workflow.add_node("judge", create_judge_node(judge))
    workflow.add_node("learner", create_learner_node())

    workflow.add_edge("attacker", "defender")
    workflow.add_edge("defender", "judge")
    workflow.add_edge("judge", "learner")

    def should_continue(state: RTZState) -> str:
        """Continue looping until ``done`` is set by the learner node."""
        if state.get("done", False):
            return END
        return "attacker"

    workflow.add_conditional_edges("learner", should_continue)

    workflow.set_entry_point("attacker")

    return workflow.compile()
