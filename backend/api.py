from __future__ import annotations

import os
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import sessions as S


S.init_db()

app = FastAPI(title="Multiplayer Labeling API", openapi_url="/api/openapi.json")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateSessionReq(BaseModel):
    min_budget: int = 10


class CreatePlayerReq(BaseModel):
    role: str


class LabelsReqItem(BaseModel):
    item_id: str
    label_value: str

class BulkItemsReqItem(BaseModel):
    item_id: str
    payload: str

class BulkItemsReq(BaseModel):
    items: list[BulkItemsReqItem]


BASE_URL = os.environ.get("BASE_URL", "http://localhost:8501")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/api/sessions")
def create_session(req: CreateSessionReq) -> Dict[str, Any]:
    sess = S.create_session(req.min_budget)
    join_url = f"{BASE_URL}/?session_id={sess['session_id']}"
    return {"session_id": sess["session_id"], "join_url": join_url}


@app.post("/api/sessions/{session_id}/players")
def create_player(session_id: str, req: CreatePlayerReq) -> Dict[str, str]:
    try:
        player = S.create_player(session_id, req.role)
        return player
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/sessions/{session_id}")
def get_session(session_id: str) -> Dict[str, Any]:
    sess = S.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    players = S.list_players(session_id)
    return {
        "session_id": sess["session_id"],
        "status": sess["status"],
        "min_budget": sess["min_budget"],
        "players": [
            {
                "player_id": p["player_id"],
                "display_name": p["display_name"],
                "role": p["role"],
                "status": p["status"],
            }
            for p in players
        ],
    }


@app.post("/api/sessions/{session_id}/start")
def start(session_id: str) -> Dict[str, Any]:
    try:
        out = S.start_session(session_id)
        return out
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/sessions/{session_id}/players/{player_id}/next-batch")
def next_batch(session_id: str, player_id: str) -> Dict[str, Any]:
    if not S.get_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    batch = S.get_player_batch(session_id, player_id)
    return {"items": batch}


@app.post("/api/sessions/{session_id}/players/{player_id}/labels")
def post_labels(session_id: str, player_id: str, labels: List[LabelsReqItem]) -> Dict[str, Any]:
    if not S.get_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    count = S.upsert_labels(session_id, player_id, [l.dict() for l in labels])
    return {"saved": count}


@app.get("/api/sessions/{session_id}/progress")
def get_progress(session_id: str) -> Dict[str, Any]:
    try:
        return S.progress(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/sessions/{session_id}/next")
def host_next(session_id: str) -> Dict[str, str]:
    if not S.get_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    S.complete_session(session_id)
    return {"status": "completed"}

@app.post("/api/items/bulk")
def bulk_items(req: BulkItemsReq) -> Dict[str, int]:
    pairs = [(it.item_id, it.payload) for it in req.items]
    n = S.seed_items_from_list(pairs)
    return {"inserted": n}


class PoolSample(BaseModel):
    sample_id: str
    dataset: str
    table: str
    row: int
    col: str
    val: str | None = None


@app.post("/api/sessions/{session_id}/pool")
def set_pool(session_id: str, samples: List[PoolSample]) -> Dict[str, int]:
    if not S.get_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    count = S.save_session_pool(session_id, [s.dict() for s in samples])
    return {"saved": count}


@app.get("/api/sessions/{session_id}/pool")
def get_pool(session_id: str) -> Dict[str, Any]:
    if not S.get_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"samples": S.get_session_pool(session_id)}


@app.get("/api/sessions/{session_id}/labels")
def get_merged_labels(session_id: str) -> Dict[str, Any]:
    if not S.get_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"labels": S.merged_labels(session_id)}


def run_in_background(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Optional helper to start the API in-process (Streamlit page can call)."""
    import threading
    import uvicorn

    def _run():
        uvicorn.run(app, host=host, port=port, log_level="warning")

    t = threading.Thread(target=_run, daemon=True)
    t.start()
