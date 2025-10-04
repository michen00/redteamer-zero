"""Utilities for rendering RedTeamer Zero reports as simple HTML."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from pathlib import Path


def render_simple(records: Iterable[Mapping[str, Any]]) -> str:
    """Render iterable trace ``records`` into a minimal HTML report.

    Args:
        records: Iterable containing mapping-like trace entries.

    Returns:
        HTML document as a string.
    """
    data = list(records)
    return f"""
<!doctype html>
<html>
<head>
  <meta charset='utf-8'>
  <title>RTZ Report</title>
  <style>
    body {{
      font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
      margin: 2rem;
    }}
    .card {{
      border: 1px solid #ddd;
      border-radius: 8px;
      padding: 1rem;
      margin-bottom: 1rem;
    }}
    pre {{
      white-space: pre-wrap;
    }}
  </style>
</head>
<body>
  <h1>RedTeamer Zero Report</h1>
  <div class="card">Total events: {len(data)}</div>
  <pre id="data">{json.dumps(data, indent=2)}</pre>
</body>
</html>
"""


def write_html(records: Iterable[Mapping[str, Any]], out_path: Path) -> None:
    """Render ``records`` and persist them to ``out_path`` as HTML.

    Args:
        records: Iterable of mapping-like trace entries.
        out_path: Destination path for the generated HTML.
    """
    html = render_simple(records)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
