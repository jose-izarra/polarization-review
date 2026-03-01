# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Start API server
poe start          # uvicorn src.api.main:app --reload on :8000

# Tests
poe test           # Run all tests with pytest
pytest tests/test_normalize.py -v   # Run a single test file
pytest tests/test_llm_assess.py::test_function_name -v  # Run a single test

# Code quality
poe lint           # ruff check
poe fix            # ruff check --fix
poe format         # ruff format
```

Dependencies are managed with `uv`. Run `uv sync` after changing any `pyproject.toml`.

## Architecture

Monorepo with two workspace members: `src/api` and `src/internal/pipeline`.

**Request lifecycle:**
1. `POST /analyze` → stores `SearchRequest` in a dict, returns `task_id`, spawns background thread
2. Background thread calls `run_search(request)` and streams progress via `asyncio.Queue`
3. Client connects via `WS /ws/{task_id}` to receive JSON status messages until `complete` or `error`

**Pipeline stages** (`src/internal/pipeline/llm/run_search.py`):
1. **Collect** — 3 scrapers (Reddit, GNews, YouTube) run concurrently via `ThreadPoolExecutor`, results merged and normalized to `NormalizedItem` list (top 40 by engagement)
2. **Assess** — `llm_assess.assess_items()` sends items to Gemini in batches of 15, scoring each for `sentiment` (1–5), `stance` (−1/0/1), `animosity` (1–5), then computes `r = stance * (sentiment + 0.5 * animosity)`
3. **Score** — `score.compute_polarization()` returns `std_dev(r_values) / P_MAX * 100` where `P_MAX = 7.5`
4. **Confidence** — `base = 1.0 if n≥10 else 0.4`, multiplied by `opinionated_ratio`; result capped at 0.4 for low samples

**Key types** (`src/internal/pipeline/llm/types.py`):
- `SearchRequest` — query + scraping parameters
- `NormalizedItem` — unified schema across all sources (id, text, url, timestamp, engagement, platform)
- `ItemScore` — per-item LLM output (sentiment, stance, animosity, r)
- `PolarizationResult` — final output (score 0–100, confidence, rationale, evidence snippets, status)

## Environment

Copy `.env.example` to `.env`. Required for full functionality:
- `GEMINI_API_KEY` — LLM assessment (required)
- `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET` — Reddit scraper
- `YOUTUBE_API_KEY` — YouTube scraper
- `GNEWS_API_KEY` — GNews scraper
- `POLARIZATION_MODEL` — optional, defaults to `gemini-2.5-flash`

## Test conventions

All tests live in `tests/`. They mock `call_model` to avoid real API calls. Import paths use `src.internal.pipeline.llm.*` and `src.internal.pipeline.scrape.*`.
