import streamlit as st
import logging
import time
import json
import os
from typing import Dict, Any, List

from streamlit_swipecards import streamlit_swipecards
from backend import backend_sample_labeling
from components import render_sidebar, apply_base_styles, get_datasets_path, render_restart_expander, render_inline_restart_button, get_swipecard_colors
from components.utils import mark_pipeline_dirty

# Logger setup (console only)
logger = logging.getLogger("labeling")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    _handler.setFormatter(_formatter)
    logger.addHandler(_handler)
logger.setLevel(logging.INFO)

# Page setup
st.set_page_config(page_title="Labeling", layout="wide")
st.title("Labeling")

# Apply base styles
apply_base_styles()

# Sidebar navigation
render_sidebar()

## Multiplayer handling moved to pages/05_Multi_PlayerLabel.py

# Load dataset and labeling budget from pipeline configuration if available
if "pipeline_path" in st.session_state:
    cfg_path = os.path.join(st.session_state.pipeline_path, "configurations.json")
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path) as f:
                cfg = json.load(f)
            selected = cfg.get("selected_dataset")
            if selected and "dataset_select" not in st.session_state:
                st.session_state.dataset_select = selected
            # Ensure labeling budget is hydrated from config if missing in session
            if "labeling_budget" not in st.session_state and cfg.get("labeling_budget") is not None:
                st.session_state.labeling_budget = int(cfg.get("labeling_budget", 10))
        except Exception:
            pass

# If dataset remains undefined, warn user and provide a navigation button
if "dataset_select" not in st.session_state:
    st.warning("⚠️ Pipeline not configured.")
    if st.button("Go back to Configurations"):
        st.switch_page("pages/Configurations.py")
    st.stop()

dataset = st.session_state.dataset_select

# Session-state keys
SAMPLE_KEY = "labeling.sampled_cells"
SAMPLE_DATASET_KEY = "labeling.sampled_cells.dataset"
SAMPLE_BUDGET_KEY = "labeling.sampled_cells.budget"

# Hydrate domain_folds and cell_folds from pipeline config on reload
if ("domain_folds" not in st.session_state or not st.session_state.get("domain_folds")) and "pipeline_path" in st.session_state:
    cfg_path = os.path.join(st.session_state.pipeline_path, "configurations.json")
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path) as f:
                cfg = json.load(f)
            st.session_state.domain_folds = cfg.get("domain_folds", {})
        except Exception:
            pass

if ("cell_folds" not in st.session_state or not st.session_state.get("cell_folds")) and "pipeline_path" in st.session_state:
    cfg_path = os.path.join(st.session_state.pipeline_path, "configurations.json")
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path) as f:
                cfg = json.load(f)
            if cfg.get("cell_folds"):
                st.session_state.cell_folds = cfg.get("cell_folds")
        except Exception:
            pass


def make_card(cell: Dict[str, Any]) -> Dict[str, Any]:
    """Return a table-mode card configuration for streamlit-swipecards."""

    datasets_path = get_datasets_path(dataset)
    dataset_path = os.path.join(datasets_path, cell["table"], "clean.csv")

    row = int(cell.get("row", 0))
    column = cell.get("col", "")

    return {
        "dataset_path": dataset_path,
        "row_index": row,
        "name": cell.get("name", ""),
        "description": f"Value: {cell.get('val', '')}",
        "highlight_cells": [{"row": row, "column": column}],
        "highlight_rows": [{"row": row}],
        "highlight_columns": [{"column": column}],
        "center_table_row": row,
        "center_table_column": column,
    }


def _compute_sampled_cells(
    dataset: str,
    labeling_budget: int,
    cell_folds: Dict[str, Any],
    domain_folds: Dict[str, Any],
):
    # Log only when actually computing (i.e., cache miss)
    logger.info(
        "Sampling cells via backend_sample_labeling (dataset=%s, budget=%s)",
        dataset,
        labeling_budget,
    )
    return backend_sample_labeling(
        selected_dataset=dataset,
        labeling_budget=labeling_budget,
        cell_folds=cell_folds,
        domain_folds=domain_folds,
    )


@st.cache_data(show_spinner=False)
def get_cached_sampled_cells(
    dataset: str,
    labeling_budget: int,
    cell_folds: Dict[str, Any],
    domain_folds: Dict[str, Any],
):
    return _compute_sampled_cells(dataset, labeling_budget, cell_folds, domain_folds)


def run_sampling():
    with st.spinner("🔄 Processing... Please wait..."):
        labeling_budget = st.session_state.get("labeling_budget", 10)
        cell_folds = st.session_state.get("cell_folds", {})
        domain_folds = st.session_state.get("domain_folds", {})
        sampled_cells = get_cached_sampled_cells(
            dataset=dataset,
            labeling_budget=labeling_budget,
            cell_folds=cell_folds,
            domain_folds=domain_folds,
        )
        # Persist in session state to avoid re-sampling on reload
        st.session_state[SAMPLE_KEY] = sampled_cells
        st.session_state[SAMPLE_DATASET_KEY] = dataset
        st.session_state[SAMPLE_BUDGET_KEY] = labeling_budget
        # Small delay to make spinner visible and UX smooth
        time.sleep(0.3)

# Migration: support prior non-namespaced key
if "sampled_cells" in st.session_state and SAMPLE_KEY not in st.session_state:
    st.session_state[SAMPLE_KEY] = st.session_state["sampled_cells"]
    st.session_state[SAMPLE_DATASET_KEY] = dataset
    st.session_state[SAMPLE_BUDGET_KEY] = st.session_state.get("labeling_budget", 10)

# Auto-run sampling only if no samples exist for the current dataset
_current_budget = st.session_state.get("labeling_budget", 10)
if (
    SAMPLE_KEY not in st.session_state
    or st.session_state.get(SAMPLE_DATASET_KEY) != dataset
    or st.session_state.get(SAMPLE_BUDGET_KEY) != _current_budget
):
    run_sampling()

if SAMPLE_KEY in st.session_state:
    cards: List[Dict[str, Any]] = st.session_state.get(SAMPLE_KEY, [])
    # Log: initializing cards (console)
    logger.info(
        "Initializing cards (n=%s, dataset=%s, budget=%s)",
        len(cards),
        st.session_state.get(SAMPLE_DATASET_KEY),
        st.session_state.get(SAMPLE_BUDGET_KEY),
    )
    card_data = [c for c in (make_card(card) for card in cards) if c]

    st.info(
        "Swipe left to mark as error, swipe right to mark as correct.")

    results = streamlit_swipecards(
        cards=card_data, 
        display_mode="table", 
        view="desktop", 
        key="labeling_cards",
        last_card_message="No more cards to swipe, continue with the Next-button below.",
        colors=get_swipecard_colors()
    )

    if "labeling_results" not in st.session_state:
        st.session_state.labeling_results = {}

    if results and isinstance(results.get("swipedCards", None), list):
        swipes = results.get("swipedCards", [])
        made_changes = False
        for swipe in swipes:
            idx = swipe.get("index")
            action = swipe.get("action")
            if idx is not None and action in {"left", "right"} and idx < len(cards):
                # Support legacy/multiplayer shapes without 'id'
                c = cards[idx]
                card_id = c.get("id") or c.get("sample_id") or f"{c.get('table')}|{c.get('row')}|{c.get('col')}|{c.get('val')}"
                key = str(card_id)
                new_val = action == "right"
                prev_val = st.session_state.labeling_results.get(key)
                if prev_val is None or prev_val != new_val:
                    st.session_state.labeling_results[key] = new_val
                    made_changes = True
        if made_changes:
            # Only mark dirty if we actually recorded new swipes in this render
            mark_pipeline_dirty()

    st.markdown("---")
    nav_cols = st.columns([1, 1, 1], gap="small")

    # Restart: confirmation dialog to go to app.py
    with nav_cols[0]:
        render_inline_restart_button(page_id="labeling", use_container_width=True)

    # Back: to Quality Based Folding
    if nav_cols[1].button("Back", key="labeling_back", use_container_width=True):
        st.switch_page("pages/QualityBasedFolding.py")

    # Next: go to Propagated Errors (propagation triggered there)
    if nav_cols[2].button("Next", key="labeling_next", use_container_width=True):
        st.switch_page("pages/PropagatedErrors.py")
