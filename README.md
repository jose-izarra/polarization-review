# polarization-review

A polarization analysis pipeline that collects public discourse from multiple sources (Reddit, GNews, YouTube), uses LLM assessment to score sentiment, stance, and animosity, and produces a polarization score with supporting evidence.

## How it works

1. **Collect** — Scrapers run concurrently via `ThreadPoolExecutor`, each returning normalized items. Results are merged, capped at 20 items per platform, and balanced by source lean (GNews) or stance (YouTube)
2. **Relevance filter** — LLM filters out items not relevant to the query (batches of 25)
3. **Assess** — LLM scores each item for sentiment (1–5), stance (−1/0/1), and animosity (1–5) in batches of 15
4. **Echo chamber dampening** — Reduces animosity weight by 0.7× for YouTube comments whose stance matches their parent video's stance
5. **Score** — Computes a polarization score (0–100) using population standard deviation of per-item `r` values (see [Scoring formula](#scoring-formula))
6. **Confidence** — Rates confidence (high/moderate/low/very\_low) based on sample size

## Setup

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) for dependency management

### Install dependencies

```bash
uv sync --all-packages
```

### Environment variables

Copy `.env.example` to `.env` and fill in the required keys:

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | Yes | LLM assessment via Gemini |
| `REDDIT_CLIENT_ID` | Yes | Reddit scraper |
| `REDDIT_CLIENT_SECRET` | Yes | Reddit scraper |
| `YOUTUBE_API_KEY` | Yes | YouTube scraper |
| `GNEWS_API_KEY` | Yes | GNews scraper |
| `POLARIZATION_MODEL` | No | Defaults to `gemini-2.5-flash` |

## Usage

### Start the API server

```bash
poe start
```

Runs `uvicorn src.api.main:app --reload` on port 8000.

### Endpoints

#### `POST /analyze`

Submit a query. Returns a `task_id` immediately; processing runs in the background.

**Request body:**

| Field | Type | Default | Description |
|---|---|---|---|
| `query` | string | required | Topic to analyze |
| `time_filter` | `"day"` \| `"week"` \| `"month"` | `"month"` | Time window for scraping |
| `max_posts` | int (1–200) | `30` | Max posts to collect |
| `max_comments_per_post` | int (1–200) | `10` | Max comments per post |
| `mode` | `"live"` \| `"fake_polarized"` \| `"fake_moderate"` \| `"fake_neutral"` | `"live"` | Use synthetic data instead of live scraping (useful for testing without API keys) |

**Response:** `{ "task_id": "<uuid>" }`

#### `WS /ws/{task_id}`

WebSocket that streams JSON progress messages until `complete` or `error`:

```json
{ "status": "collecting | assessing | scoring | complete | error", "message": "...", "result": null }
```

On `complete`, `result` contains the full `PolarizationResult`.

### Run tests

```bash
poe test
```

Or run a specific test file:

```bash
pytest tests/test_normalize.py -v
```

### Code quality

```bash
poe lint      # ruff check
poe fix       # ruff check --fix
poe format    # ruff format
```

## Scoring formula

Each item gets a polarity value `r`:

```
r_i = stance × (sentiment + α × animosity)    [α = 0.8]
```

where `stance ∈ {−1, 0, 1}`, `sentiment ∈ [1, 5]`, `animosity ∈ [1, 5]`.

Only opinionated items (`stance ≠ 0`) contribute to the spread calculation. The final score scales by the fraction of opinionated items to avoid inflating scores from fringe feuds in otherwise neutral samples:

```
opinionated_ratio = n_opinionated / n_total
score = pstdev({r_i | stance ≠ 0}) × opinionated_ratio / P_MAX × 100   (capped at 100)
```

`P_MAX = 7.5` is the calibrated normalization bound. A perfectly one-sided sample scores 0 (zero spread). An all-neutral sample also scores 0. The score is highest when opinions are evenly and strongly split between opposing sides.

## Architecture

### Workspace layout

This is a `uv` monorepo with three workspace members:

```
src/
  api/                     # FastAPI application
  internal/
    pipeline/              # Scraping, LLM assessment, scoring
    config/                # Shared configuration
```

### Scraper adapters

Each data source is implemented as a `SourceAdapter` (defined in `src/internal/pipeline/scrape/base.py`):

```python
class SourceAdapter(Protocol):
    name: str

    def fetch(self, query: str, config: dict) -> list[NormalizedItem]: ...
    def build_config(self, request: SearchRequest) -> dict: ...
    def post_process(self, items: list[NormalizedItem], query: str, **kwargs) -> list[NormalizedItem]: ...
```

Adapters self-register via their package `__init__.py`:

```python
# src/internal/pipeline/scrape/mysource/__init__.py
from ..registry import register_source
from .adapters import MySourceAdapter

register_source("mySource", MySourceAdapter())
```

The pipeline discovers all registered adapters at runtime via `get_sources()` — no changes to `run_search.py` are needed.

### Adding a new source

1. Create `src/internal/pipeline/scrape/<source>/` with:
   - `fetch.py` — raw API calls, return a dict with `{"data": {"posts": [...], "comments": [...]}}`
   - `utils.py` — constants and helpers
   - `adapters.py` — implement `SourceAdapter` (the three methods above)
   - `__init__.py` — call `register_source("<name>", <AdapterInstance>())`
2. Add the required API key to `.env.example` and document it in this README
3. In `build_config`, translate `SearchRequest` fields to source-specific parameters
4. In `post_process`, apply any source-specific balancing (e.g. bias controls). Only operate on `item.platform == self.name`
5. Add a test file at `tests/test_<source>_scraper.py` following the pattern in `test_gnews_scraper.py`

### Key data types

All types live in `src/internal/pipeline/domain.py`.

**`NormalizedItem`** — unified schema every adapter must return:

| Field | Type | Description |
|---|---|---|
| `id` | `str` | Unique item ID (e.g. `"reddit_post_abc123"`) |
| `text` | `str` | Cleaned text content |
| `url` | `str` | Source URL |
| `timestamp` | `str` | ISO 8601 datetime |
| `engagement_score` | `int` | Upvotes/likes (0 if unavailable) |
| `content_type` | `"post"` \| `"comment"` | Item type |
| `platform` | `str` | `"reddit"` \| `"youtube"` \| `"gnews"` |
| `source_lean` | `str \| None` | `"left"` \| `"center"` \| `"right"` \| `"unknown"` (GNews only) |
| `relevance_score` | `float \| None` | Set to `1.0` by the relevance filter if kept |
| `parent_video_id` | `str \| None` | YouTube only — ID of the parent video (for comments) |
| `parent_video_stance` | `int \| None` | YouTube only — stance of parent video, used for echo chamber dampening |

**`ItemScore`** — per-item LLM output:

| Field | Type | Description |
|---|---|---|
| `id` | `str` | Matches `NormalizedItem.id` |
| `sentiment` | `int` | 1–5 |
| `stance` | `int` | −1 (against) / 0 (neutral) / 1 (for) |
| `animosity` | `int` | 1–5 |
| `r` | `float` | `stance × (sentiment + 0.8 × animosity)` |
| `reason` | `str` | One-sentence LLM explanation |

## Testing conventions

All tests live in `tests/`. LLM calls are mocked — never make real API calls in tests.

The standard pattern is to patch `call_model` at the module level:

```python
@patch("src.internal.pipeline.llm.llm_assess.call_model")
def test_something(mock_call_model):
    mock_call_model.return_value = ...
```

Test files by module:

| File | Covers |
|---|---|
| `test_score.py` | Polarization formula edge cases |
| `test_validate.py` | Synthetic dataset generation and known-topic validation |
| `test_llm_assess.py` | Scoring and relevance filter |
| `test_run_search.py` | End-to-end pipeline with mocked stages |
| `test_normalize.py` | Text cleaning, dedup, field extraction |
| `test_gnews_scraper.py` | GNews API and source lean lookup |
| `test_youtube_scraper.py` | YouTube API, transcripts, parent_video_id |

To run the validation suite (synthetic formula checks):

```python
python -c "from src.internal.pipeline.llm.validate import run_known_topics; print(run_known_topics())"
```

## Ablation studies

Ablation studies are used to isolate how specific components of the pipeline affect polarization scores. To keep experiments reproducible and comparable, every ablation must follow a shared structure.

### Required study structure

Each study lives in its own folder inside `studies/` and must include both a runner and a config file:

```text
studies/
  <study_name>/
    run.py
    config.json
```

- `run.py` is the study entrypoint and is responsible for executing the ablation
- `config.json` stores the parameters that control the study behavior

### `run.py` expectations

When creating a new study runner:

1. Load all tunable values from `config.json` (avoid hardcoded experiment settings)
2. Run baseline and ablated variants in a consistent, repeatable way
3. Write outputs into `studies/<study_name>/results/` for later comparison
4. Keep study logic isolated to the study folder whenever possible

### `config.json` expectations

Use `config.json` as the single source of truth for experiment parameters. Typical keys include:

- Topics or datasets to run
- Number of runs / repetitions
- Random seed(s)
- Feature toggles for the ablation (what is enabled/disabled)
- Output file/folder settings

A minimal example:

```json
{
  "name": "disable_relevance_filter",
  "topics": ["abortion", "gun control", "ai regulation"],
  "runs": 5,
  "seed": 42,
  "ablation": {
    "disable_relevance_filter": true
  },
  "output_dir": "data/results"
}
```

### Results format (standard across all studies)

To make cross-study comparison easy, every study should produce the same two output formats in `studies/<study_name>/results/`:

- `<label>_<timestamp>.json` (machine-readable, canonical record)
- `<label>_<timestamp>.txt` (human-readable report)

#### Required JSON structure

Every results JSON should contain:

- `config`: resolved config used for that run batch
- `runs`: dictionary from condition/scenario label to per-run result list
- `stats`: aggregate stats per condition/scenario (`mean`, `std`, `min`, `max`, `total_runs`)

Each per-run result should include at least:

- `run`
- `polarization_score`
- `sample_size`
- `rationale`
- `stance_distribution` (`for`, `against`, `neutral`)
- `stance_averages`
- `source_breakdown`
- `elapsed_seconds`
- `status`
- `error` (nullable)

#### Required TXT structure

The TXT report should mirror the JSON contents with:

1. Study header (description/date/context such as query, model, or scenarios)
2. Per-condition sections with per-run score details
3. Stance distribution + stance averages
4. Source/platform breakdown
5. Aggregate section and summary table (mean/std/min/max)

### Study-specific fields

Study-specific details are encouraged, but they should be additive so the common schema stays stable.

Examples of useful extra fields:

- platform-cap studies: `items_after_cap`, `items_after_filter`, `n_collected`
- model-comparison studies: `model_label`, `model_id`, `provider`, `scenario`
- source-ablation studies: `sources` labels or source subset metadata

### Adding a new ablation study

1. Create `studies/<new_study_name>/`
2. Add `run.py` and `config.json`
3. Add a `results/` subfolder and emit both `.json` and `.txt` outputs with the standard format
4. Define the exact baseline-vs-ablation change in config and implement it in `run.py`
5. Keep naming and outputs consistent so studies can be compared across runs
6. Document any study-specific assumptions near the study folder (or in `docs/` if broader)

## Further reading

Detailed documentation is in [`docs/`](./docs/):
