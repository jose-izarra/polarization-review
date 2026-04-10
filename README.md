# polarization-review

A polarization analysis pipeline that collects public discourse from multiple sources (Reddit, GNews, YouTube), uses LLM assessment to score sentiment, stance, and animosity, and produces a polarization score with supporting evidence.

## How it works

1. **Collect** — Scrapers run concurrently via `ThreadPoolExecutor`, each returning normalized items. Results are merged, capped at 100 items per platform, and balanced by source lean (GNews) or stance (YouTube)
2. **Relevance filter** — LLM filters out items not relevant to the query (batches of 25)
3. **Assess** — LLM scores each item for sentiment (1–5), stance (−1/0/1), and animosity (1–5) in batches of 15
4. **Echo chamber dampening** — Reduces animosity weight by 0.7× for YouTube comments whose stance matches their parent video's stance
5. **Score** — Computes a polarization score (0–100) using population standard deviation of per-item `r` values (see [Scoring formula](#scoring-formula))

## Setup

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) for dependency management

### Install dependencies

```bash
uv sync --all-packages
```

### Environment variables

Copy `.env.example` to `.env` and fill in the required keys:

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | Yes (default) | LLM assessment via Gemini |
| `REDDIT_CLIENT_ID` | Yes | Reddit scraper |
| `REDDIT_CLIENT_SECRET` | Yes | Reddit scraper |
| `YOUTUBE_API_KEY` | Yes | YouTube scraper |
| `GNEWS_API_KEY` | Yes | GNews scraper |
| `POLARIZATION_MODEL` | No | Defaults to `gemini-2.5-flash` |
| `OPENAI_API_KEY` | No | Required when using GPT models |
| `QWEN_API_KEY` | No | Required when using Qwen models |
| `MISTRAL_API_KEY` | No | Required when using Mistral models |
| `DEEPSEEK_API_KEY` | No | Required when using DeepSeek models |
| `OLLAMA_HOST` | No | Ollama base URL (default: `http://localhost:11434`) |

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
| `max_comments_per_post` | int (1–200) | `30` | Max comments per post |
| `mode` | `"live"` \| `"fake_*"` | `"live"` | Use synthetic data instead of live scraping. See [Mock data](#mock-data) for valid `fake_*` values |

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
poe test tests/test_normalize.py
```

### Code quality

```bash
poe lint      # ruff check
poe fix       # ruff check --fix
poe format    # ruff format
```

## Makefile commands

Two convenience targets wrap common multi-topic workflows:

### `run-pipeline-topics`

Run the full pipeline (collect → filter → assess → score) for one or more topics in parallel (up to 4 at a time). Each topic is passed as a `--topic` override to `scripts/run_pipeline.py`, which reads all other settings from `scripts/run_pipeline_config.json`.

```bash
make run-pipeline-topics TOPICS="abortion,gun control,inflation"
```

### `assess-all-topics`

Run the assess → score stages on pre-collected item files (skips scraping). Processes up to 4 files in parallel. The list of files is controlled by the `ASSESS_ITEMS` variable in the Makefile. Optionally attach a note to all runs.

```bash
make assess-all-topics
make assess-all-topics NOTE="baseline run"
```

## Scripts

All scripts read their configuration from JSON files in `scripts/` — edit those files rather than passing CLI arguments (except where noted).

| Script | Config file | Description |
|---|---|---|
| `collect_items.py` | `pipeline_config.json` (`collect` key) | Fetches live data from Reddit, GNews, and YouTube for each topic in the config, applies the relevance filter, and saves normalized items to `data/items_{topic}.json`. Skips a topic if its output file already exists. |
| `run_pipeline.py` | `run_pipeline_config.json` | Runs the full pipeline (collect → filter → assess → score) for a single query, repeated `runs` times. Accepts `--topic` to override the query from config, and `--config` to point at a different config file. Outputs a `.txt` report. |
| `assess_from_file.py` | `pipeline_config.json` (`assess` key) | Loads an existing `data/items_*.json` file and runs only the assess → post-process → score stages. Takes the file path as a positional argument and an optional `--note`. Saves a numbered run report to `data/results/`. |
| `compute_score.py` | `compute_score_config.json` | Manual score calculator. Edit the config with item counts, sentiment, and animosity values to compute what the formula would return — useful for sanity-checking formula changes without running the full pipeline. |
| `run_fake_scenario.py` | *(no config file — CLI flags only)* | Runs fake scenarios through the real LLM pipeline and writes a combined `.txt` summary to `scripts/results/`. Accepts `--dataset` (`general` \| `fictitious` \| `real_context`), `--model`, and `--note`. |

## Mock data

`src/internal/pipeline/mock/` contains synthetic datasets for testing the pipeline without live scrapers or real-world topics. There are three dataset families, each with three polarization levels:

| Mode key | Family | Expected score |
|---|---|---|
| `fake_polarized_fictitious` | Fictitious (FlobberFlopper lore) | ~100 |
| `fake_moderate_fictitious` | Fictitious | ~35–70 |
| `fake_neutral_fictitious` | Fictitious | ~0 |
| `fake_polarized_general` | General (universal language, fictional topics) | ~100 |
| `fake_moderate_general` | General | ~35–70 |
| `fake_neutral_general` | General | ~0 |
| `fake_polarized_real_context` | Real-world topics | ~100 |
| `fake_moderate_real_context` | Real-world topics | ~35–70 |
| `fake_neutral_real_context` | Real-world topics | ~0 |

**Fictitious** scenarios use the entirely invented Kingdom of FlobberFloppers universe (King Flavio, Snorf Tax, Wumble Festival, etc.) so the LLM cannot rely on prior knowledge — scores must come from the text content alone.

**General** scenarios use universally understood strong/mild language applied to fictional topics — a middle ground that is legible to any LLM without domain-specific lore.

**Real-context** scenarios use structurally identical content applied to real-world topics (Donald Trump, Federal Carbon Tax, New Orleans Mardi Gras) to test how real-world LLM priors interact with the scoring.

Pass any mode key as the `mode` field in `POST /analyze`, or use `SearchRequest(mode=<key>)` directly in code.

## Pre-collected data (`data/`)

`data/` stores normalized item files produced by `collect_items.py`. Each file (`items_{topic}.json`) contains the full list of `NormalizedItem` objects that passed the relevance filter for a given topic, ready for the assess stage.

```json
{ "query": "gun control", "items": [ ... ] }
```

Assessment results from `assess_from_file.py` are written to `data/results/` as numbered `.txt` run reports.

## Multi-model support

The pipeline supports multiple LLM providers. Set `POLARIZATION_MODEL` in `.env` or in a script config to switch providers. Provider detection is automatic based on the model name prefix:

| Prefix | Provider | Example model |
|---|---|---|
| `gemini-*` (default) | Google Gemini | `gemini-2.5-flash` |
| `gpt-*`, `o1`, `o3`, `o4` | OpenAI | `gpt-4o`, `o3-mini` |
| `qwen-*` | Alibaba Qwen (DashScope) | `qwen-plus` |
| `mistral-*`, `codestral-*`, `ministral-*` | Mistral AI | `mistral-large-latest` |
| `deepseek-*` | DeepSeek | `deepseek-chat` |
| `ollama/*` | Ollama (local) | `ollama/llama3.2:1b` |

If the relevant API key is not set, the pipeline falls back to mock responses automatically.

For Ollama, pull the model first (`ollama pull llama3.2:1b`) and ensure Ollama is running locally.

## Scoring formula

Each item gets a polarity value `r`:

```
r_i = stance × (sentiment + animosity)
```

where `stance ∈ {−1, 0, 1}`, `sentiment ∈ [1, 5]`, `animosity ∈ [1, 5]`.

Only opinionated items (`stance ≠ 0`) contribute to the spread calculation. The final score scales by an effective participation ratio that down-weights neutral items (with `NEUTRAL_WEIGHT = 0.5`) to avoid inflating scores from fringe feuds in otherwise neutral samples:

```
effective_total = n_opinionated + 0.5 × n_neutral
opinionated_ratio = n_opinionated / effective_total
score = pstdev({r_i | stance ≠ 0}) × opinionated_ratio / P_MAX × 100   (capped at 100)
```

`P_MAX = 10` (maximum `r` magnitude: `|stance| × (sentiment_max + animosity_max) = 1 × (5 + 5)`). A perfectly one-sided sample scores 0 (zero spread). An all-neutral sample also scores 0. The score is highest when opinions are evenly and strongly split between opposing sides.

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
| `r` | `float` | `stance × (sentiment + animosity)` |
| `reason` | `str` | One-sentence LLM explanation |

## Testing conventions

All tests live in `tests/`. LLM calls are mocked — never make real API calls in tests.

The standard pattern is to patch `assess_items` and `filter_relevant_items` at the `run` module level:

```python
@patch("src.internal.pipeline.llm.run.assess_items")
@patch("src.internal.pipeline.llm.run.filter_relevant_items")
def test_something(mock_filter, mock_assess):
    mock_assess.return_value = ...
    mock_filter.return_value = ...
```

To run the validation suite (synthetic formula checks):

```python
uv run python -c "from src.internal.pipeline.llm.validate import run_known_topics; print(run_known_topics())"
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
