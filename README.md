# polarization-review

A polarization analysis pipeline that collects public discourse from multiple sources (Reddit, GNews, YouTube), uses LLM assessment to score sentiment, stance, and animosity, and produces a polarization score with supporting evidence.

## How it works

1. **Collect** — Scrapes Reddit, GNews, and YouTube concurrently, merges results into a normalized list (top 40 by engagement), and balances GNews items by source lean
2. **Relevance filter** — LLM filters out items not relevant to the query
3. **Assess** — LLM scores each item for sentiment (1–5), stance (−1/0/1), and animosity (1–5)
4. **Echo chamber dampening** — Reduces animosity weight for YouTube comments that match their parent video's stance
5. **Score** — Computes a polarization score (0–100) from distribution balance, animosity, and opinionated ratio
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

**Endpoints:**
- `POST /analyze` — Submit a query, returns a `task_id`
- `WS /ws/{task_id}` — WebSocket for streaming progress and results

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
