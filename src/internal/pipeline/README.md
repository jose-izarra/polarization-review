# Pipeline Module

Core data pipeline for collecting, normalizing, scoring, and summarizing polarization across online sources.

## Directory Structure

```
src/internal/pipeline/
├── domain.py                  # All shared dataclasses (SearchRequest, NormalizedItem, etc.)
├── scrape/                    # Data collection layer (scrapers + plugin registry)
│   ├── base.py                # SourceAdapter protocol
│   ├── registry.py            # Adapter registration and lookup
│   ├── normalize.py           # Shared text cleaning + NormalizedItem construction
│   ├── gnews/                 # GNews scraper
│   ├── reddit/                # Reddit scraper
│   └── youtube/               # YouTube scraper
├── llm/                       # LLM processing layer
│   ├── client.py              # Gemini API wrapper (call_llm)
│   ├── run.py                 # Pipeline orchestrator (run_search)
│   ├── assess.py              # Relevance filter + per-item scoring
│   ├── normalize.py           # Dedup, quality filter, top-N selection
│   ├── score.py               # Polarization formula (compute_polarization)
│   ├── validate.py            # Synthetic formula checks
│   └── sources/               # Source-specific LLM post-processors (plugin registry)
│       ├── base.py            # LLMSourceProcessor protocol
│       ├── registry.py        # Processor registration and lookup
│       └── youtube/           # YouTube echo chamber dampening
└── mock/                      # Fake data and deterministic mock LLM
    ├── llm.py                 # mock_call_model (no API key required)
    ├── data.py                # Scenario aggregator
    ├── data_fictitious.py     # FlobberFloppers universe scenarios
    └── data_general.py        # General-language scenarios
```

## Key Data Types (`domain.py`)

All pipeline stages communicate through these dataclasses:

| Type | Purpose |
|---|---|
| `SearchRequest` | User query + scraping parameters (time_filter, max_posts, mode) |
| `NormalizedItem` | Unified item schema across all sources |
| `ItemScore` | Per-item LLM output: sentiment, stance, animosity, r, reason |
| `EvidenceItem` | Enriched evidence item for final output |
| `PolarizationResult` | Final output: score 0–100, confidence, rationale, evidence list |

### `NormalizedItem` Fields

```python
id: str                          # Unique item ID
text: str                        # Cleaned body text
url: str                         # Source URL
timestamp: str                   # ISO 8601
engagement_score: int            # Upvotes, views, likes (source-dependent)
content_type: Literal["post", "comment"]
platform: str                    # "reddit" | "youtube" | "gnews"
source_lean: str | None          # "left" | "center" | "right" | None
relevance_score: float | None    # Set to 1.0 after relevance filter passes
parent_video_id: str | None      # YouTube comments only
```

### `ItemScore` Fields

```python
id: str
sentiment: int       # 1–5: how positive/negative the tone is
stance: int          # -1 (against) / 0 (neutral) / 1 (for)
animosity: int       # 1–5: emotional intensity / hostility
r: float             # stance * (sentiment + α * animosity), α=0.8
reason: str          # 1-sentence LLM explanation
```

## Pipeline Stages (`llm/run.py`)

`run_search(request: SearchRequest) -> PolarizationResult` orchestrates all stages:

### 1. Collect & Normalize

Three scrapers run concurrently in a `ThreadPoolExecutor`:

- **Reddit** — discovers relevant subreddits, fetches posts + top-level comments
- **GNews** — fetches news articles, balances by source political lean (max 10 per lean)
- **YouTube** — generates 3 perspective-covering search queries, fetches videos + comments

Each scraper implements `SourceAdapter` (see [Extending: New Scrapers](#adding-a-new-scraper)).

After collection, items are deduplicated by ID, quality-filtered (min 20 chars, no `[deleted]`), and the top 20 per platform are kept.

### 2. Relevance Filter

`filter_relevant_items()` in `assess.py` sends items to the LLM in batches of 25 and discards off-topic items. Kept items get `relevance_score = 1.0`.

### 3. Assess

`assess_items()` sends items to Gemini in batches of 15. Each item is scored for:
- `sentiment` (1–5): positivity/negativity of tone
- `stance` (-1/0/1): opposition, neutrality, or support for the topic
- `animosity` (1–5): emotional hostility
- `r` is computed as: `stance * (sentiment + α * animosity)` where **α = 0.8** (`ALPHA_DEFAULT` in `assess.py`)

JSON parsing failures trigger one retry with a stricter prompt.

### 4. Source-Specific Post-Processing

LLM source processors (see [Extending: New Processors](#adding-a-new-llm-processor)) run after the main assessment. The built-in YouTube processor:

1. `determine_video_stances()` — classifies each video's stance via LLM
2. `apply_echo_chamber_dampening()` — multiplies animosity by **0.7×** for comments whose stance matches their parent video (echo chamber signal)

### 5. Score

`compute_polarization(item_scores)` in `score.py`:

```
P = pstdev(r_opinionated) * opinionated_ratio / P_MAX * 100
```

- `pstdev` = population standard deviation of `r` for items where `stance ≠ 0`
- `opinionated_ratio` = n_opinionated / n_total (scales down fringe feuds)
- `P_MAX = 7.5` (calibration constant)
- All-neutral or single-sided → `pstdev = 0` → score = 0

### 6. Confidence

```python
confidence = min(n_relevant / 10, 1.0)
```

Labels: `very_low` (<5 items), `low` (5–9), `moderate` (10–29), `high` (≥30).

## Scraper Module (`scrape/`)

### Plugin Registry

All scrapers register themselves via `scrape/registry.py`. Registration happens as a side effect of importing the scraper package. `run.py` triggers this with:

```python
import src.internal.pipeline.scrape  # registers all adapters
```

### `SourceAdapter` Protocol (`scrape/base.py`)

```python
class SourceAdapter(Protocol):
    name: str  # "reddit" | "gnews" | "youtube"

    def fetch(self, query: str, config: dict) -> list[NormalizedItem]: ...
    def build_config(self, request: SearchRequest) -> dict: ...
    def post_process(self, items: list[NormalizedItem], query: str) -> list[NormalizedItem]: ...
```

### GNews (`scrape/gnews/`)

- **Entry:** `collect_gnews_data(query, time_filter)` in `fetch.py`
- **Env:** `GNEWS_API_KEY`
- **Post-process:** Caps items per source lean (left/center/right) to prevent political bias
- **Source lean lookup:** `SOURCE_LEAN_LOOKUP` in `utils.py` maps ~23 news domains to lean

### Reddit (`scrape/reddit/`)

- **Entry:** `collect_reddit_data(search_term, scrape_config, reddit)` in `fetch.py`
- **Env:** `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`
- **Strategy:** Phase 1 discovers relevant subreddits; Phase 2 fetches posts from r/all and top-discovered subreddits; Phase 3 fetches comments from top posts
- **Config presets** in `utils.py`: `DEFAULT_CONFIG`, `QUICK_CONFIG`, `THOROUGH_CONFIG`, `HISTORICAL_CONFIG`

### YouTube (`scrape/youtube/`)

- **Entry:** `collect_youtube_data(query, config, queries)` in `fetch.py`
- **Env:** `YOUTUBE_API_KEY`
- **Strategy:** Uses LLM (`generate_youtube_queries()`) to create 3 perspective-diverse queries; paginates if not enough videos with comments
- **Post-process:** `_balance_youtube_by_stance()` caps videos to 4 per stance using LLM classification

## LLM Client (`llm/client.py`)

Single entry point for all LLM calls:

```python
call_llm(system_prompt, user_payload, model=None, _override=None) -> str
```

- If `GEMINI_API_KEY` is unset (local mode), falls back to `mock_call_model`
- `_override` accepts a callable — used in tests to inject fake responses
- Temperature: 0.0 (deterministic)

## LLM Source Processors (`llm/sources/`)

### `LLMSourceProcessor` Protocol (`llm/sources/base.py`)

```python
class LLMSourceProcessor(Protocol):
    name: str

    def post_assess(
        self,
        query: str,
        items: list[NormalizedItem],
        scores: list[ItemScore],
        call_model=None,
    ) -> list[ItemScore]: ...
```

Processors registered via `llm/sources/registry.py` are called automatically by `run.py` after the main assessment.

## Mock Module (`mock/`)

Used for local development and deterministic testing:

- **`mock_call_model`** — detects prompt type (relevance/assessment/stances/queries) and returns a fixed cycling response pattern
- **Fake scenarios** — 3 scenarios × 2 language variants:

| Mode | Expected Score | Description |
|---|---|---|
| `fake_polarized_*` | ~100 | 10 items per side, high animosity |
| `fake_moderate_*` | ~35–70 | Mixed sides, moderate animosity |
| `fake_neutral_*` | ~0 | All-neutral or balanced + low animosity |

  - `_fictitious`: FlobberFloppers lore (King Flavio, Snorf Tax, Wumble Festival) — LLM can't use prior knowledge
  - `_general`: Universal strong language — LLM assesses accurately

## Validation Suite (`llm/validate.py`)

Run formula checks against synthetic scenarios:

```bash
python -c "from src.internal.pipeline.llm.validate import run_known_topics; print(run_known_topics())"
```

`generate_synthetic_dataset(n_for, n_against, n_neutral, animosity_level)` creates controlled `ItemScore` lists for unit testing the formula independently of the LLM.

## Extending the Pipeline

### Adding a New Scraper

1. Create `src/internal/pipeline/scrape/{name}/`
2. Implement `SourceAdapter`:

```python
# scrape/{name}/adapters.py
from ..base import SourceAdapter
from ..registry import register_source
from src.internal.pipeline.domain import NormalizedItem, SearchRequest

class MyAdapter:
    name = "mysource"

    def fetch(self, query: str, config: dict) -> list[NormalizedItem]:
        # Fetch + return normalized items
        ...

    def build_config(self, request: SearchRequest) -> dict:
        return {"max_items": request.max_posts, ...}

    def post_process(self, items: list[NormalizedItem], query: str) -> list[NormalizedItem]:
        return items  # Optional balancing/filtering
```

3. Register in `scrape/{name}/__init__.py`:

```python
from .adapters import MyAdapter
from ..registry import register_source
register_source("mysource", MyAdapter())
```

4. Import in `scrape/__init__.py` (triggers registration):

```python
from . import gnews, reddit, youtube, mysource
```

5. Add tests in `tests/test_mysource_scraper.py` — mock all external API calls.

### Adding a New LLM Processor

1. Create `src/internal/pipeline/llm/sources/{name}/`
2. Implement `LLMSourceProcessor`:

```python
# llm/sources/{name}/processor.py
class MyProcessor:
    name = "mysource"

    def post_assess(self, query, items, scores, call_model=None):
        # Adjust scores after main assessment
        return scores
```

3. Register in `llm/sources/{name}/__init__.py`:

```python
from .processor import MyProcessor
from ..registry import register
register(MyProcessor())
```

4. Import in `llm/sources/__init__.py` (triggers registration).

### Changing the Polarization Formula

1. Edit `score.py:compute_polarization()`
2. Update `_P_MAX` if the score distribution shifts
3. Re-run the validation suite and update `test_score.py` / `test_validate.py`
4. Document the change in `docs/FORMULA_EVOLUTION.md`

### Adding a New Field to Items or Results

1. Add the field to the relevant dataclass in `domain.py`
2. Populate it in the scraper adapter's `fetch()` or `normalize_raw_item()`
3. Thread it through any pipeline stages that need it
4. Update `_build_evidence()` in `run.py` if it belongs in the final output
5. Add or update tests

## Testing

Tests live in `tests/`. All external API calls must be mocked — no real network calls in tests.

### Mocking LLM Calls

Use the `_override` parameter:

```python
def fake_call(system_prompt, user_payload):
    items = json.loads(user_payload)
    return json.dumps([{"id": i["id"], "sentiment": 3, "stance": 1, "animosity": 2, "reason": "ok"} for i in items])

scores = assess_items("query", items, model="...", _override=fake_call)
```

### Common Test Helpers

```python
def _make_item(id: str, text: str = "Sample text", platform: str = "reddit") -> NormalizedItem:
    return NormalizedItem(id, text, "https://x", "2026-01-01T00:00:00", 10, "post", platform, None, None, None)

def _item_score(id: str, stance: int = 1, animosity: int = 2) -> ItemScore:
    r = stance * (3 + 0.8 * animosity)
    return ItemScore(id=id, sentiment=3, stance=stance, animosity=animosity, r=r, reason="test")
```

### Running Tests

```bash
poe test                        # All tests
pytest tests/test_score.py -v  # Single file
pytest tests/test_llm_assess.py::TestRelevanceFilter -v  # Single class
```
