"""Konfigurasi dari environment variable."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    data_file: Path
    log_level: str

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            data_file=Path(os.getenv("LIFETRACK_DATA_FILE", "data/lifetrack.json")),
            log_level=os.getenv("LIFETRACK_LOG_LEVEL", "WARNING").upper(),
        )
