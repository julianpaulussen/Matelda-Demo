import json
import os
import random
import string
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from .backend import (
    backend_sample_labeling,
    backend_label_propagation,
)


def _sessions_dir(pipeline_path: str) -> str:
    d = os.path.join(pipeline_path, "sessions")
    os.makedirs(d, exist_ok=True)
    return d


def _session_path(pipeline_path: str, session_id: str) -> str:
    return os.path.join(_sessions_dir(pipeline_path), f"{session_id}.json")


def _load_session(pipeline_path: str, session_id: str) -> Dict[str, Any]:
    p = _session_path(pipeline_path, session_id)
    if not os.path.exists(p):
        return {}
    with open(p, "r") as f:
        return json.load(f)


def _save_session(pipeline_path: str, session_id: str, data: Dict[str, Any]) -> None:
    p = _session_path(pipeline_path, session_id)
    tmp = p + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, p)


def _random_session_code(k: int = 6) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(k))


ADJECTIVES = [
    "Brave",
    "Calm",
    "Swift",
    "Clever",
    "Witty",
    "Mighty",
    "Gentle",
    "Happy",
    "Nimble",
    "Bold",
]

ANIMALS = [
    "Fox",
    "Panda",
    "Otter",
    "Eagle",
    "Tiger",
    "Koala",
    "Dolphin",
    "Hawk",
    "Lynx",
    "Bison",
]


def _unique_display_name(existing: List[str]) -> str:
    # Ensure uniqueness by trying combinations; fallback to suffixing
    for _ in range(200):
        name = f"{random.choice(ADJECTIVES)}{random.choice(ANIMALS)}{random.randint(0, 9999):04d}"
        if name not in existing:
            return name
    # Fallback
    base = f"Player{random.randint(0, 9999):04d}"
    i = 1
    while f"{base}-{i}" in existing:
        i += 1
    return f"{base}-{i}"


def create_session(
    pipeline_path: str,
    dataset: str,
    labeling_budget: int,
    cell_folds: Dict[str, Dict[str, List[Dict[str, Any]]]],
    domain_folds: Dict[str, List[str]],
) -> Tuple[str, str]:
    """Create a new multiplayer session. Returns (session_id, host_player_id)."""
    session_id = _random_session_code()
    host_id = str(uuid.uuid4())
    now = int(time.time())
    # Generate a friendly random host display name
    host_display = _unique_display_name([])
    data = {
        "id": session_id,
        "created_at": now,
        "pipeline_path": pipeline_path,
        "dataset": dataset,
        "status": "waiting",  # waiting -> running -> finished
        "labeling_budget": labeling_budget,
        "domain_folds": domain_folds,
        "cell_folds": cell_folds,
        "host_id": host_id,
        "players": {
            host_id: {
                "id": host_id,
                "name": host_display,
                "is_host": True,
                "status": "joined",  # joined -> labeling -> done
                "assigned": [],
                "labels": [],
            }
        },
    }
    _save_session(pipeline_path, session_id, data)
    return session_id, host_id


def get_session(pipeline_path: str, session_id: str) -> Dict[str, Any]:
    return _load_session(pipeline_path, session_id)


def join_session(
    pipeline_path: str, session_id: str
) -> Tuple[Optional[str], Optional[str]]:
    data = _load_session(pipeline_path, session_id)
    if not data or data.get("status") not in {"waiting", "running"}:
        return None, None
    # Prevent joining after labeling started if no assignments remain
    existing_names = [p.get("name", "") for p in data.get("players", {}).values()]
    display = _unique_display_name(existing_names)
    pid = str(uuid.uuid4())
    data["players"][pid] = {
        "id": pid,
        "name": display,
        "is_host": False,
        "status": "joined",
        "assigned": [],
        "labels": [],
    }
    _save_session(pipeline_path, session_id, data)
    return pid, display


def list_players(pipeline_path: str, session_id: str) -> List[Dict[str, Any]]:
    data = _load_session(pipeline_path, session_id)
    return list(data.get("players", {}).values()) if data else []


def start_session(
    pipeline_path: str, session_id: str
) -> Dict[str, Any]:
    """Finalize roster, sample total pool based on labeling_budget, and assign per player uniquely."""
    data = _load_session(pipeline_path, session_id)
    if not data:
        return {}
    if data.get("status") == "running":
        return data

    dataset = data["dataset"]
    labeling_budget = int(data.get("labeling_budget", 10))
    cell_folds = data.get("cell_folds", {})
    domain_folds = data.get("domain_folds", {})

    players = [p for p in data["players"].values()]
    if not players:
        return data

    # Total budget is split across players as evenly as possible
    n = len(players)
    base = labeling_budget // n
    remainder = labeling_budget % n

    # Sample a pool the size of total budget; if pool is smaller, fallback to sample as many as available
    pool = backend_sample_labeling(
        selected_dataset=dataset,
        labeling_budget=labeling_budget,
        cell_folds=cell_folds,
        domain_folds=domain_folds,
    )

    # Assign unique items per player
    random.shuffle(pool)
    cursor = 0
    for idx, p in enumerate(players):
        k = base + (1 if idx < remainder else 0)
        assigned = pool[cursor : cursor + k]
        cursor += k
        data["players"][p["id"]]["assigned"] = assigned
        data["players"][p["id"]]["status"] = "labeling"

    data["status"] = "running"
    _save_session(pipeline_path, session_id, data)
    return data


def submit_player_labels(
    pipeline_path: str,
    session_id: str,
    player_id: str,
    labels: List[Dict[str, Any]],
) -> Dict[str, Any]:
    data = _load_session(pipeline_path, session_id)
    if not data:
        return {}
    player = data.get("players", {}).get(player_id)
    if not player:
        return data
    player["labels"] = labels
    player["status"] = "done"
    _save_session(pipeline_path, session_id, data)
    return data


def all_players_done(pipeline_path: str, session_id: str) -> bool:
    data = _load_session(pipeline_path, session_id)
    if not data:
        return False
    return all(p.get("status") == "done" for p in data.get("players", {}).values())


def aggregate_labels_for_propagation(
    pipeline_path: str, session_id: str
) -> Tuple[str, List[Dict[str, Any]]]:
    data = _load_session(pipeline_path, session_id)
    if not data:
        return "", []
    dataset = data.get("dataset", "")
    all_labels: List[Dict[str, Any]] = []
    for p in data.get("players", {}).values():
        for label in p.get("labels", []):
            # Ensure the expected schema for backend_label_propagation
            all_labels.append(
                {
                    "table": label.get("table"),
                    "row": label.get("row", 0),
                    "col": label.get("col", ""),
                    "val": label.get("val", ""),
                    "is_error": bool(label.get("is_error", False)),
                    "domain_fold": label.get("domain_fold", ""),
                    "cell_fold": label.get("cell_fold", ""),
                    "cell_fold_label": label.get("cell_fold_label", "neutral"),
                }
            )
    return dataset, all_labels


def run_propagation_for_session(
    pipeline_path: str, session_id: str
) -> Dict[str, Any]:
    dataset, labels = aggregate_labels_for_propagation(pipeline_path, session_id)
    if not dataset:
        return {}
    return backend_label_propagation(dataset, labels)
