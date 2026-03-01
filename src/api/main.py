from __future__ import annotations

import asyncio
import json
from typing import Literal
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from src.internal.pipeline.llm.run_search import run_search
from src.internal.pipeline.llm.types import SearchRequest

from src.internal.config.logger import logfire


app = FastAPI(title="Polarization Review API", version="0.1")

logfire.instrument_fastapi(app)

app.get("/")(lambda: {"message": "Hello, World!"})

# task_id -> asyncio.Queue of progress message dicts
_task_queues: dict[str, asyncio.Queue] = {}


class AnalyzeRequest(BaseModel):
    query: str = Field(..., min_length=1)
    time_filter: Literal["day", "week", "month"] = "week"
    max_posts: int = Field(30, ge=1, le=200)
    max_comments_per_post: int = Field(10, ge=1, le=200)


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

    try:
        await emit("collecting", "Collecting and normalizing Reddit data...")

        search_request = SearchRequest(
            query=body.query,
            time_filter=body.time_filter,
            max_posts=body.max_posts,
            max_comments_per_post=body.max_comments_per_post,
        )

        await emit("assessing", "Scoring items with LLM...")

        result = await asyncio.to_thread(run_search, search_request)

        await emit("scoring", "Computing polarization score...")
        await emit("complete", "Analysis complete.", result.to_dict())

    except Exception as exc:
        await emit("error", f"Analysis failed: {exc}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
