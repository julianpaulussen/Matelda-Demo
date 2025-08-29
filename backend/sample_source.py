from __future__ import annotations

"""
Host-only sampling hook for multiplayer start.

Implements backend_sample_labeling(total_samples) by reusing the app's
existing backend.backend_sample_labeling with the most recent pipeline
configuration under pipelines/<name>/configurations.json.
"""
import json
import os
from typing import Any, Dict, List

from .backend import backend_sample_labeling as single_sample


def _latest_pipeline_dir() -> str | None:
    root = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pipelines")
    try:
        dirs = [os.path.join(root, d) for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))]
        dirs = [d for d in dirs if os.path.exists(os.path.join(d, "configurations.json"))]
        if not dirs:
            return None
        dirs.sort(key=lambda d: os.path.getmtime(d), reverse=True)
        return dirs[0]
    except Exception:
        return None


def _load_config(pipeline_dir: str) -> Dict[str, Any]:
    cfg = {}
    try:
        with open(os.path.join(pipeline_dir, "configurations.json"), "r") as f:
            cfg = json.load(f)
    except Exception:
        pass
    return cfg


def backend_sample_labeling(total_samples: int, pipeline_cfg: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    """Return a list of item payloads for multiplayer assignments.

    total_samples = min_budget * num_players
    """
    cfg = pipeline_cfg or {}
    if not cfg:
        latest = _latest_pipeline_dir()
        if latest:
            cfg = _load_config(latest)

    selected_dataset = cfg.get("selected_dataset") or "Demo"
    domain_folds = cfg.get("domain_folds", {})
    cell_folds = cfg.get("cell_folds", {})

    # Reuse single-player sampler with a budget equal to total samples
    items = single_sample(
        selected_dataset=selected_dataset,
        labeling_budget=int(total_samples),
        cell_folds=cell_folds,
        domain_folds=domain_folds,
    )

    # Ensure a stable id field named 'id' and include dataset for frontend rendering
    for i, it in enumerate(items):
        if "id" not in it:
            it["id"] = f"itm-{i}"
        it.setdefault("selected_dataset", selected_dataset)
    return items

