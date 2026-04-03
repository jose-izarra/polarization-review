import logfire

import src.internal.config.logger  # noqa: F401 — triggers logfire setup
from src.internal.config.config import config  # noqa: F401

__all__ = ["logfire", "config"]
