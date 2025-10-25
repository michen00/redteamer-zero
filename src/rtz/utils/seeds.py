"""Helpers for synchronizing random seeds across optional backends."""

from __future__ import annotations

import os
import random

# Optional dependencies (NumPy, PyTorch) for reproducible seeding.
try:  # pragma: no cover - numpy optional
    import numpy as np
except ImportError:  # pragma: no cover - numpy optional
    np = None

try:  # pragma: no cover - torch optional
    import torch
except ImportError:  # pragma: no cover - torch optional
    torch = None


def set_seed(seed: int, *, deterministic: bool = True) -> None:
    """Set global RNG seeds across common libraries for reproducibility.

    Args:
        seed: base integer seed
        deterministic: if True, set envs and backend flags for determinism when possible
    """
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)

    if np is not None:
        np.random.seed(seed)

    if torch is not None:
        torch.manual_seed(seed)
        if hasattr(torch, "cuda") and hasattr(torch.cuda, "manual_seed_all"):
            torch.cuda.manual_seed_all(seed)
        if deterministic:
            use_deterministic = getattr(torch, "use_deterministic_algorithms", None)
            if callable(use_deterministic):
                use_deterministic(mode=True)
                os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
