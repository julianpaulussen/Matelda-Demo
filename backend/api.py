"""
FastAPI app and programmatic Uvicorn startup helper for Multiplayer Labeling.

Implements /api endpoints and starts in a background thread when requested
via ensure_api_started().
"""
from __future__ import annotations

import os
import threading
import time
from typing import Any, Dict, List, Optional
import socket
import http.client

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .sample_source import backend_sample_labeling
from . import sessions as S


def _api_host() -> str:
    return os.environ.get("API_HOST", "127.0.0.1")


_CURRENT_PORT: Optional[int] = None


def _api_port() -> int:
    try:
        return int(_CURRENT_PORT or int(os.environ.get("API_PORT", "8000")))
    except Exception:
        return 8000


def api_base() -> str:
    return f"http://{_api_host()}:{_api_port()}/api"


def _port_in_use(host: str, port: int, timeout: float = 0.2) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def _check_health(host: str, port: int, timeout: float = 0.4) -> bool:
    try:
        conn = http.client.HTTPConnection(host, port, timeout=timeout)
        conn.request("GET", "/api/health")
        resp = conn.getresponse()
        ok = resp.status == 200
        conn.close()
        return ok
    except Exception:
        return False


class CreateSessionBody(BaseModel):
    min_budget: int


class CreatePlayerBody(BaseModel):
    role: str


class LabelsBodyItem(BaseModel):
    item_id: str
    label_value: str
    order_index: int


app = FastAPI(title="Matelda Multiplayer API", openapi_url="/api/openapi.json")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _on_startup() -> None:
    S.init_db()


@app.get("/api/health")
def health() -> Dict[str, Any]:
    return {"status": "ok"}

# Back-compat alias
@app.get("/health")
def health_alias() -> Dict[str, Any]:
    return {"status": "ok"}


@app.post("/api/sessions")
def api_create_session(body: CreateSessionBody) -> Dict[str, Any]:
    sess = S.create_session(min_budget=int(body.min_budget))
    sid = sess["session_id"]
    base_url = os.environ.get("BASE_URL", "http://localhost:8501")
    join_url = f"{base_url}/?session_id={sid}"
    return {"session_id": sid, "join_url": join_url}


@app.post("/api/sessions/{session_id}/players")
def api_create_player(session_id: str, body: CreatePlayerBody) -> Dict[str, Any]:
    try:
        player = S.create_player(session_id=session_id, role=body.role)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return player


@app.post("/api/sessions/{session_id}/players/{player_id}/done")
def api_mark_player_done(session_id: str, player_id: str) -> Dict[str, Any]:
    """Mark a player as done even if they haven't labeled all assignments."""
    try:
        S.set_player_done(session_id, player_id)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/sessions/{session_id}")
def api_get_session(session_id: str) -> Dict[str, Any]:
    sess = S.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="session not found")
    players = S.list_players(session_id)
    return {
        "session_id": sess["session_id"],
        "status": sess["status"],
        "min_budget": sess["min_budget"],
        "players": [dict(p) for p in players],
    }


@app.post("/api/sessions/{session_id}/start")
def api_start(session_id: str) -> Dict[str, Any]:
    """Transition session to preparing and build pool+assignments in background.

    Players can poll /sessions/{sid} and /players/{pid}/next-batch; they'll
    receive items once status becomes 'active'.
    """
    sess = S.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="session not found")

    status = sess["status"]
    if status == "active":
        return {"ok": True, "status": "active"}
    if status == "preparing":
        return {"ok": True, "status": "preparing"}

    players = S.list_players(session_id)
    if not players:
        raise HTTPException(status_code=400, detail="no players registered")
    min_budget = int(sess["min_budget"])
    total_needed = min_budget * len(players)

    def _worker() -> None:
        try:
            pool = S.get_session_pool(session_id)
            if len(pool) < total_needed:
                items = backend_sample_labeling(total_needed)
                samples = [
                    {
                        "sample_id": str(it.get("id")),
                        "dataset": it.get("selected_dataset") or it.get("dataset") or "Demo",
                        "table": it.get("table"),
                        "row": int(it.get("row", 0)),
                        "col": it.get("col"),
                        "val": it.get("val"),
                    }
                    for it in items
                ]
                S.save_session_pool(session_id, samples)
            S.start_session(session_id)
        except Exception:
            # On failure, reset back to lobby so host can retry
            try:
                S.set_status(session_id, "lobby")
            except Exception:
                pass

    # Flip to preparing and spawn background worker
    S.set_status(session_id, "preparing")
    t = threading.Thread(target=_worker, name=f"mp-prepare-{session_id}", daemon=True)
    t.start()
    return {"ok": True, "status": "preparing"}


@app.get("/api/sessions/{session_id}/players/{player_id}/next-batch")
def api_next_batch(session_id: str, player_id: str) -> Dict[str, Any]:
    items = S.get_player_batch(session_id, player_id)
    if items is None:
        raise HTTPException(status_code=404, detail="not found")
    last_index = S.count_player_labels(session_id, player_id)
    return {"items": items, "last_index": int(last_index)}


@app.post("/api/sessions/{session_id}/players/{player_id}/labels")
def api_labels(session_id: str, player_id: str, body: List[LabelsBodyItem]) -> Dict[str, Any]:
    items = [i.dict() for i in body]
    saved = S.upsert_labels(session_id, player_id, items)
    return {"saved": saved}


@app.get("/api/sessions/{session_id}/progress")
def api_progress(session_id: str) -> Dict[str, Any]:
    return S.progress(session_id)


@app.post("/api/sessions/{session_id}/next")
def api_next(session_id: str) -> Dict[str, Any]:
    # If all labelers are done, export merged labels atomically
    meta = S.progress(session_id)
    exported = False
    if meta.get("all_done"):
        try:
            _export_session_labels(session_id)
            exported = True
        except Exception:
            exported = False
    S.complete_session(session_id)
    return {"ok": True, "exported": exported}


def _export_session_labels(session_id: str) -> str:
    """Write merged labels to pipelines/ as JSON via atomic replace."""
    labels = S.merged_labels(session_id)
    root = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pipelines")
    os.makedirs(root, exist_ok=True)
    out_path = os.path.join(root, f"multiplayer_labels_{session_id}.json")
    tmp_path = out_path + ".tmp"
    payload = {"session_id": session_id, "labels": labels}
    with open(tmp_path, "w", encoding="utf-8") as f:
        import json as _json
        _json.dump(payload, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, out_path)
    return out_path


_SERVER_THREAD: Optional[threading.Thread] = None
_SERVER_STARTED = False


def ensure_api_started() -> str:
    """Start the API once and return base URL. Reuse if already running.

    - If configured port responds to /api/health, reuse it.
    - If port is occupied but not healthy, pick a free port.
    """
    global _SERVER_THREAD, _SERVER_STARTED, _CURRENT_PORT

    host = _api_host()
    configured = int(os.environ.get("API_PORT", "8000"))

    # If something is already listening and healthy, reuse it
    if _check_health(host, configured):
        _CURRENT_PORT = configured
        _SERVER_STARTED = True
        return api_base()

    # If we already tried to start, but health is not OK, fall through and try a new port

    # Decide a port: if configured is free, use it; else pick an ephemeral free port
    if not _port_in_use(host, configured):
        chosen = configured
    else:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, 0))
            chosen = s.getsockname()[1]

    _CURRENT_PORT = chosen

    if not _SERVER_STARTED:
        _SERVER_STARTED = True
        import uvicorn

        def _run(p: int):
            uvicorn.run(app, host=host, port=p, log_level="warning")

        t = threading.Thread(target=_run, args=(chosen,), name="mp-api", daemon=True)
        t.start()
        _SERVER_THREAD = t
        time.sleep(0.25)

    return api_base()
