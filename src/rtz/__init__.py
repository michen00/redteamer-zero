"""RedTeamer Zero: A self-play jailbreak lab with attacker, defender, and auditor agents.

This module provides a framework for red teaming language models through self-play.
It includes components for attacking models, defending against attacks, and evaluating
model behavior under adversarial conditions.

Modules:
    attack: Tools and strategies for generating adversarial prompts.
    defense: Techniques for detecting and mitigating adversarial inputs.
    harness: Infrastructure for running and evaluating models.
    judge: Components for evaluating model outputs and attack success.
    models: Model definitions and utilities.
    orchestration: High-level workflows for running experiments.
    reports: Utilities for generating reports and analyzing results.
    utils: Shared utility functions and helpers.
"""

__all__ = [
    "attack",
    "defense",
    "harness",
    "judge",
    "models",
    "orchestration",
    "reports",
    "utils",
]
