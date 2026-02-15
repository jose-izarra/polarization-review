# polarization-review

Minimal v0 polarization proof-of-concept pipeline.

## What it does
- Uses one source: Reddit (`r/all`)
- Performs minimal cleaning/dedup/ranking
- Makes one LLM batch call to assess polarization
- Returns UI-ready JSON: score, confidence, rationale, evidence

## Run CLI
```bash
python3 -m src.pipeline.run_search "immigration policy"
```

Optional flags:
- `--time-filter day|week|month` (default: `week`)
- `--max-posts` (default: `30`)
- `--max-comments-per-post` (default: `10`)

## Run API
```bash
uvicorn src.pipeline.api:app --reload
```

Endpoint:
- `GET /analyze?query=immigration%20policy`

## Required environment variables
Reddit collection:
- `REDDIT_CLIENT_ID`
- `REDDIT_CLIENT_SECRET`
- `REDDIT_USER_AGENT` (optional)

LLM assessment:
- `OPENAI_API_KEY`
- `POLARIZATION_MODEL` (optional, default: `gpt-4o-mini`)

## Run tests
```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```
