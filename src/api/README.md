# API Module

FastAPI server that exposes the polarization pipeline over HTTP + WebSocket. Clients submit a query, receive a `task_id`, then stream progress updates until the result is ready.

## Directory Structure

```
src/api/
├── main.py      # FastAPI app, all endpoints, background task execution
├── models.py    # Pydantic request/response models
└── cache.py     # Thread-safe in-memory result cache
```

## Endpoints

### `POST /analyze`

Accepts a search request, enqueues a background task, and immediately returns a `task_id`.

**Request body (`AnalyzeRequest`):**

```json
{
  "query": "string (required)",
  "time_filter": "day | week | month (default: month)",
  "max_posts": "int 1–200 (default: 30)",
  "max_comments_per_post": "int 1–200 (default: 10)",
  "mode": "live | fake_polarized_general | fake_moderate_general | fake_neutral_general (default: live)"
}
```

**Response:**

```json
{ "task_id": "uuid-string" }
```

The `fake_*` modes bypass scraping and use pre-built synthetic data for demo and testing purposes. The `fake_*_fictitious` variants (FlobberFloppers lore) are intentionally excluded from the public API — they are for internal benchmark use only.

### `WS /ws/{task_id}`

WebSocket stream for a running task. Each message is a JSON object:

```json
{
  "status": "collecting | assessing | scoring | complete | error",
  "message": "Human-readable progress string",
  "result": null
}
```

On `complete`, `result` contains the full `PolarizationResult`. On `error`, `result` is `null` and `message` describes the failure. The server closes the socket after either terminal status.

**Status sequence (happy path):**
```
collecting → assessing → scoring → complete
```

### `GET /`

Health check. Returns `{"message": "Hello, World!"}`.

## Request Lifecycle

```
POST /analyze
    │
    ├─ Check cache (same query + params + today's date)
    │   └─ Cache hit → return existing task_id immediately
    │
    ├─ mark_pending() — claim this query; if already pending, wait for that task
    │
    └─ Spawn background thread → _run_analysis_task(task_id, body)
            │
            ├─ run_search(SearchRequest(...))   ← pipeline module
            │   └─ Emits status updates via asyncio.Queue at each stage
            │
            ├─ store_result(result) → cache
            │
            └─ Signal asyncio.Event → wake any waiting duplicate requests

WS /ws/{task_id}
    └─ Pulls messages from Queue until "complete" or "error", then closes
```

## Caching (`cache.py`)

Results are cached in memory for the lifetime of the process. Cache keys include the normalized query (lowercased + stripped), today's date (daily expiry), and all request parameters.

| Function | Purpose |
|---|---|
| `get_cached_result(...)` | Returns a hit or `None` |
| `mark_pending(...) -> bool` | Claims a query; returns `False` if already claimed or cached |
| `wait_for_pending(...)` | Awaits another task's completion for the same query |
| `store_result(...)` | Writes to cache and signals any waiters |
| `clear_pending(...)` | Removes the pending marker on error (still signals waiters to unblock them) |

Duplicate concurrent requests for the same query are deduplicated: the second request waits on `asyncio.Event` and reads the result once the first task finishes.

The cache is **in-memory only** — it does not survive server restarts and is not shared across processes.

## Configuration

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `CORS_ORIGINS` | Yes | Comma-separated list of allowed origins (e.g. `http://localhost:3000`) |
| `GEMINI_API_KEY` | Production | Google Gemini API key for LLM calls |
| `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` | Production | Reddit API credentials |
| `YOUTUBE_API_KEY` | Production | YouTube Data API v3 key |
| `GNEWS_API_KEY` | Production | GNews API key |
| `POLARIZATION_MODEL` | No | Gemini model name (default: `gemini-2.5-flash`) |
| `ENV` | No | Set to `local` for mock LLM mode; `test` for real credentials in tests |
| `LOGFIRE_TOKEN` | No | Logfire token for structured logging |

### Local Development

```bash
# .env
ENV=local
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

With `ENV=local`, the pipeline uses `mock_call_model` — no API keys are required. All `fake_*` modes work without any credentials.

### Starting the Server

```bash
poe start   # uvicorn src.api.main:app --reload on :8000
```

## Adding a New Endpoint

1. Add a function to `main.py` decorated with `@app.{method}("/path")`:

```python
@app.get("/results/{task_id}")
async def get_result(task_id: str):
    result = _results.get(task_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Not found")
    return result
```

2. Define a Pydantic model in `models.py` if the endpoint has a request body or structured response:

```python
class MyResponse(BaseModel):
    task_id: str
    score: float | None
```

3. Add the response model to the decorator: `@app.get("/path", response_model=MyResponse)`.

4. Write tests against the FastAPI `TestClient`:

```python
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_my_endpoint():
    response = client.get("/results/nonexistent")
    assert response.status_code == 404
```

## Adding a New `mode`

Modes let clients request fake/synthetic data instead of live scraping. To add one:

1. Add the literal to `AnalyzeRequest.mode` in `models.py`:

```python
mode: Literal[
    "live",
    "fake_polarized_general",
    "fake_moderate_general",
    "fake_neutral_general",
    "fake_my_new_scenario",   # ← new
] = "live"
```

2. Add corresponding fake data in `src/internal/pipeline/mock/data.py` and ensure `run_search()` handles the new mode string.

## CORS

CORS is configured via `CORSMiddleware`. Update `CORS_ORIGINS` in your environment to allow additional origins. All methods and headers are permitted; credentials are allowed.

## Logging

Logfire is instrumented via `logfire.instrument_fastapi(app)`. All requests are traced automatically. Sensitive fields (`api_key`, `token`, `secret`) are scrubbed before logging.

## Testing

Use `fastapi.testclient.TestClient` for synchronous endpoint tests. For WebSocket tests, use `TestClient` as a context manager:

```python
with client.websocket_connect(f"/ws/{task_id}") as ws:
    data = ws.receive_json()
    assert data["status"] in ("collecting", "complete", "error")
```

Mock `run_search` at the import path used in `main.py` to avoid real pipeline execution in API-level tests.
