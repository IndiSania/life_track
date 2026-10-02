"""Penyimpanan JSON dengan tulis atomik."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

EMPTY_STATE: dict[str, list[dict[str, Any]]] = {"journal": [], "habits": [], "goals": []}


class JsonStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> dict[str, list[dict[str, Any]]]:
        state: dict[str, list[dict[str, Any]]] = {k: [] for k in EMPTY_STATE}
        if self.path.exists():
            state.update(json.loads(self.path.read_text(encoding="utf-8")))
        return state

    def save(self, state: dict[str, list[dict[str, Any]]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(state, indent=2, ensure_ascii=False)
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(payload)
        os.replace(tmp, self.path)
