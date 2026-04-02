from __future__ import annotations

import asyncio
import json
import os
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from src.internal.config import logfire
from src.internal.pipeline.llm.run_search import run_search
from src.internal.pipeline.domain import SearchRequest

from .cache import (
    clear_pending,
    get_cached_result,
    mark_pending,
    store_result,
    wait_for_pending,
)
from .models import AnalyzeRequest

app = FastAPI(title="Polarization Review API", version="0.1")

origins = [o.strip() for o in os.getenv("CORS_ORIGINS").split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logfire.instrument_fastapi(app)

app.get("/")(lambda: {"message": "Hello, World!"})

# task_id -> asyncio.Queue of progress message dicts
_task_queues: dict[str, asyncio.Queue] = {}


@app.post("/analyze")
async def analyze(body: AnalyzeRequest) -> dict:
    task_id = str(uuid4())
    queue: asyncio.Queue = asyncio.Queue()
    _task_queues[task_id] = queue
    asyncio.create_task(_run_analysis_task(task_id, body))
    return {"task_id": task_id}


@app.websocket("/ws/{task_id}")
async def ws_progress(websocket: WebSocket, task_id: str):
    if task_id not in _task_queues:
        await websocket.close(code=4004)
        return

    await websocket.accept()
    queue = _task_queues[task_id]

    try:
        while True:
            msg = await queue.get()
            await websocket.send_text(json.dumps(msg))
            if msg.get("status") in ("complete", "error"):
                break
    except WebSocketDisconnect:
        pass
    finally:
        _task_queues.pop(task_id, None)
        try:
            await websocket.close()
        except Exception:
            pass


async def _run_analysis_task(task_id: str, body: AnalyzeRequest) -> None:
    print(f"Running analysis task {task_id} with body {body}")
    queue = _task_queues.get(task_id)
    if queue is None:
        return

    async def emit(status: str, message: str, result=None):
        await queue.put({"status": status, "message": message, "result": result})
        print(f"Emitting status {status} with message {message} and result {result}")

    cache_args = (
        body.query,
        body.time_filter,
        body.max_posts,
        body.max_comments_per_post,
        body.mode,
    )

    try:
        # 1. Check cache for a completed result
        cached = get_cached_result(*cache_args)
        if cached is not None:
            await emit("collecting", "Collecting and normalizing Reddit data...")
            await emit("assessing", "Scoring items with LLM...")
            await emit("scoring", "Computing polarization score...")
            await emit("complete", "Analysis complete.", cached.to_dict())
            return

        # 2. Try to claim this query; if another task owns it, wait
        if not mark_pending(*cache_args):
            await emit("collecting", "Waiting for in-flight analysis...")
            cached = await wait_for_pending(*cache_args)
            if cached is not None:
                await emit("assessing", "Scoring items with LLM...")
                await emit("scoring", "Computing polarization score...")
                await emit("complete", "Analysis complete.", cached.to_dict())
                return
            # The in-flight task failed — fall through and run it ourselves
            mark_pending(*cache_args)

        # 3. Run the pipeline
        await emit("collecting", "Collecting and normalizing Reddit data...")

        search_request = SearchRequest(
            query=body.query,
            time_filter=body.time_filter,
            max_posts=body.max_posts,
            max_comments_per_post=body.max_comments_per_post,
            mode=body.mode,
        )

        await emit("assessing", "Scoring items with LLM...")

        result = await asyncio.to_thread(run_search, search_request)

        store_result(*cache_args, result=result)

        await emit("scoring", "Computing polarization score...")
        await emit("complete", "Analysis complete.", result.to_dict())

    except Exception as exc:
        clear_pending(*cache_args)
        await emit("error", f"Analysis failed: {exc}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
