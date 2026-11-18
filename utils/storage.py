"""
Lightweight JSON persistence helpers used by stateful cogs.
Writes atomically via a temporary file so interrupted writes do not corrupt state.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: Path, default: Any) -> Any:
    """Read JSON from disk, returning a copy of `default` if the file is missing or invalid."""
    if not path.exists():
        return json.loads(json.dumps(default))

    try:
        with path.open("r", encoding="utf-8") as fp:
            return json.load(fp)
    except (OSError, json.JSONDecodeError):
        return json.loads(json.dumps(default))


def save_json(path: Path, payload: Any) -> None:
    """Persist data as formatted UTF-8 JSON using an atomic temp-file swap."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(f"{path.suffix}.tmp")
    with tmp_path.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, indent=2, ensure_ascii=False)
    tmp_path.replace(path)
