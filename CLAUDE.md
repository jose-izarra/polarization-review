# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Start API server
poe start          # uvicorn src.api.main:app --reload on :8000

# Tests
poe test           # Run all tests with pytest
poe test tests/test_normalize.py -v   # Run a single test file
poe test tests/test_llm_assess.py::test_function_name -v  # Run a single test

# Code quality
poe lint           # ruff check
poe fix            # ruff check --fix
poe format         # ruff format

# Validation suite (synthetic formula checks)
uv run python3 -c "from src.internal.pipeline.llm.validate import run_known_topics; print(run_known_topics())"
```

Dependencies are managed with `uv`. Run `uv sync --all-packages` after changing any `pyproject.toml`.

## Architecture

Monorepo with two workspace members: `src/api` and `src/internal/pipeline`.

**Request lifecycle:**

1. `POST /analyze` → stores `SearchRequest` in a dict, returns `task_id`, spawns background thread
2. Background thread calls `run_search(request)` and streams progress via `asyncio.Queue`
3. Client connects via `WS /ws/{task_id}` to receive JSON status messages until `complete` or `error`

**Pipeline stages** (`src/internal/pipeline/llm/run_search.py`):

1. **Collect** — 3 scrapers (Reddit, GNews, YouTube) run concurrently via `ThreadPoolExecutor`, results merged and normalized to `NormalizedItem` list (top 40 by engagement), then balanced by source lean (max 10 GNews items per lean category)
2. **Relevance filter** — `llm_assess.filter_relevant_items()` sends items to LLM in batches of 25, keeps only items relevant to the query (sets `relevance_score=1.0` on kept items)
3. **Assess** — `llm_assess.assess_items()` sends items to Gemini in batches of 15, scoring each for `sentiment` (1–5), `stance` (−1/0/1), `animosity` (1–5), `reason` (1-sentence explanation), then computes `r = stance * (sentiment + 0.8 * animosity)`
4. **YouTube echo chamber dampening** — `_determine_video_stances()` gets per-video stance from LLM; `_apply_echo_chamber_dampening()` applies 0.7× weight to animosity of comments whose stance matches their parent video
5. **Score** — `score.compute_polarization()` uses: `distribution × animosity_score × opinionated_ratio × 20` (capped at 100). Distribution = `1 − |n_for − n_against| / (n_for + n_against)`. Animosity = mean animosity of opinionated items. All-neutral or all-one-side → 0.
6. **Confidence** — `min(n / 10, 1.0)` (linear ramp). Labels: high (≥30), moderate (≥10), low (≥5), very_low (<5).

**Key types** (`src/internal/pipeline/llm/types.py`):

- `SearchRequest` — query + scraping parameters
- `NormalizedItem` — unified schema across all sources (id, text, url, timestamp, engagement, content_type, platform, source_lean, relevance_score, parent_video_stance, parent_video_id)
- `ItemScore` — per-item LLM output (sentiment, stance, animosity, r, reason)
- `EvidenceItem` — enriched evidence (id, snippet, url, stance, animosity, sentiment, rationale, source_lean, platform)
- `PolarizationResult` — final output (score 0–100, confidence, confidence_label, rationale, evidence list, status)

Logger is configured in `src/internal/config/logger.py`.
Imports use `src.internal.config.logfire` for logging.

```python
from src.internal.config import logfire
logfire.info("Hello, world!")
```

**Source bias controls** (`src/internal/pipeline/scrape/gnews.py`):

- `SOURCE_LEAN_LOOKUP` maps ~22 news domains to left/center/right/unknown
- `_get_source_lean(url)` extracts domain and looks up lean
- `_balance_by_source_lean()` in `run_search.py` caps GNews items per lean category

**YouTube enhancements** (`src/internal/pipeline/scrape/youtube.py`):

- `_fetch_transcript(video_id)` uses `youtube-transcript-api` to get video transcripts (truncated to 2000 chars)
- Comments include `parent_video_id` in metadata for echo chamber detection

**Validation suite** (`src/internal/pipeline/llm/validate.py`):

- `generate_synthetic_dataset(n_for, n_against, n_neutral, animosity_level)` — controlled test data
- `run_known_topics()` — runs formula against known scenarios, returns pass/fail

## Environment

Copy `.env.example` to `.env`. Required for full functionality:

- `GEMINI_API_KEY` — LLM assessment (required)
- `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET` — Reddit scraper
- `YOUTUBE_API_KEY` — YouTube scraper
- `GNEWS_API_KEY` — GNews scraper
- `POLARIZATION_MODEL` — optional, defaults to `gemini-2.5-flash`

## Test conventions

All tests live in `tests/`. They mock `call_model` to avoid real API calls. Import paths use `src.internal.pipeline.llm.`* and `src.internal.pipeline.scrape.*`.

Test files:

- `test_score.py` — polarization formula edge cases (50/50 split, all-one-side, neutrals, animosity scaling)
- `test_validate.py` — synthetic dataset generation and known-topic validation
- `test_llm_assess.py` — scoring + relevance filter
- `test_run_search.py` — end-to-end pipeline with mocked collect/assess/filter/video-stances
- `test_normalize.py` — text cleaning, dedup, platform/source_lean/parent_video_id extraction
- `test_gnews_scraper.py` — GNews API + source lean lookup
- `test_youtube_scraper.py` — YouTube API + transcript + parent_video_id

## Ablation studies conventions

All ablation studies must live under `studies/`, and each study must have its own subfolder:

```text
studies/
  <study_name>/
    run.py
    config.json
```

Required rules for every new ablation study:

1. Create a dedicated folder at `studies/<study_name>/` (do not mix multiple studies in one folder)
2. Include `run.py` as the single entrypoint for executing that study
3. Include `config.json` for all tunable study parameters (dataset choices, topic lists, run counts, seeds, toggles, and output settings)
4. Keep study-specific logic/config inside the study folder; avoid hardcoded values that belong in `config.json`
5. Include a `results/` folder in the study directory and write outputs there

When adding a new ablation:

- Start by copying a prior study folder as a template, then rename it
- Update `config.json` first, then wire all reads in `run.py` from config values
- Document what the ablation changes relative to baseline (the exact component being removed/modified)
- Keep naming clear and comparable so multiple ablations can be run and analyzed consistently

### Result format requirements (must stay consistent across studies)

Each run must generate both:

- a machine-readable JSON file: `studies/<study_name>/results/<label>_<timestamp>.json`
- a human-readable text report: `studies/<study_name>/results/<label>_<timestamp>.txt`

JSON output must use a shared structure:

```json
{
  "config": { "...": "resolved config used for this run" },
  "runs": {
    "<condition_label>": [
      {
        "run": 1,
        "polarization_score": 0.0,
        "sample_size": 0,
        "rationale": "",
        "stance_distribution": { "for": 0, "against": 0, "neutral": 0 },
        "stance_averages": {
          "for": null,
          "against": null,
          "neutral": null
        },
        "source_breakdown": {},
        "elapsed_seconds": 0.0,
        "status": "ok",
        "error": null
      }
    ]
  },
  "stats": {
    "<condition_label>": {
      "score": { "n": 0, "mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0 },
      "elapsed": { "n": 0, "mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0 },
      "total_runs": 0
    }
  }
}
```

TXT report should mirror the same information in readable sections:

- Study header (description, date, query/model/scenario context, number of runs)
- Per-condition/per-scenario run details (score, sample size, elapsed, status, rationale)
- Stance distribution and stance averages
- Source/platform breakdown
- Aggregate summary table (mean/std/min/max by condition)

Study-specific fields are encouraged, but must be additive (do not rename or remove shared fields). Good examples:

- `items_after_cap`, `items_after_filter` for platform-cap studies
- `model_label`, `model_id`, `provider` for model-comparison studies
- `sources` or `scenario` labels for condition grouping
