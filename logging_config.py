"""Setup logging terpusat."""

from __future__ import annotations

import logging


def setup_logging(level: str = "WARNING") -> None:
    logging.basicConfig(
        level=getattr(logging, level, logging.WARNING),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
