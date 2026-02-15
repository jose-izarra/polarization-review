from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query

from src.pipeline.run_search import run_search
from src.pipeline.types import SearchRequest


app = FastAPI(title="Polarization Pipeline API", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/analyze")
def analyze(
    query: str = Query(..., min_length=1),
    time_filter: str = Query("week", pattern="^(day|week|month)$"),
    max_posts: int = Query(30, ge=1, le=200),
    max_comments_per_post: int = Query(10, ge=1, le=200),
) -> dict:
    try:
        request = SearchRequest(
            query=query,
            time_filter=time_filter,  # validated by regex above
            max_posts=max_posts,
            max_comments_per_post=max_comments_per_post,
        )
        return run_search(request).to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
