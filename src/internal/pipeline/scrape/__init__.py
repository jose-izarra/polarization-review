"""Scraping package. Importing this package registers all built-in source adapters."""
from . import reddit, gnews, youtube  # noqa: F401  — side-effect: registration
