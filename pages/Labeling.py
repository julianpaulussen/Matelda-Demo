import streamlit as st
import time
import json
import os
from typing import Dict, Any, List

from streamlit_swipecards import streamlit_swipecards
from backend import backend_sample_labeling
from components import render_sidebar, apply_base_styles, get_datasets_path, render_restart_expander, render_inline_restart_button, get_swipecard_colors
from components.utils import mark_pipeline_dirty

# Page setup
st.set_page_config(page_title="Labeling", layout="wide")
st.title("Labeling")

# Apply base styles
apply_base_styles()

# Sidebar navigation
render_sidebar()

## Multiplayer handling moved to pages/05_Multi_PlayerLabel.py

# Load dataset from pipeline config if not already in session_state
# Load dataset from pipeline configuration if available
if "dataset_select" not in st.session_state and "pipeline_path" in st.session_state:
    cfg_path = os.path.join(st.session_state.pipeline_path, "configurations.json")
    if os.path.exists(cfg_path):
        with open(cfg_path) as f:
            cfg = json.load(f)
        selected = cfg.get("selected_dataset")
        if selected:
            st.session_state.dataset_select = selected

# If dataset remains undefined, warn user and provide a navigation button
if "dataset_select" not in st.session_state:
    st.warning("⚠️ Pipeline not configured.")
    if st.button("Go back to Configurations"):
        st.switch_page("pages/Configurations.py")
    st.stop()

dataset = st.session_state.dataset_select

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


if "run_quality_folding" not in st.session_state:
    st.session_state.run_quality_folding = False

if not st.session_state.run_quality_folding:
    if st.button("Run Labeling"):
        with st.spinner("🔄 Processing... Please wait..."):
            labeling_budget = st.session_state.get("labeling_budget", 10)
            cell_folds = st.session_state.get("cell_folds", {})
            domain_folds = st.session_state.get("domain_folds", {})
            sampled_cells = backend_sample_labeling(
                selected_dataset=dataset,
                labeling_budget=labeling_budget,
                cell_folds=cell_folds,
                domain_folds=domain_folds,
            )
            st.session_state.sampled_cells = sampled_cells
            time.sleep(2)
        st.session_state.run_quality_folding = True
        st.rerun()
else:
    # Quality-based folding already completed but sampling might be missing
    if "sampled_cells" not in st.session_state:
        with st.spinner("🔄 Processing... Please wait..."):
            labeling_budget = st.session_state.get("labeling_budget", 10)
            cell_folds = st.session_state.get("cell_folds", {})
            domain_folds = st.session_state.get("domain_folds", {})
            sampled_cells = backend_sample_labeling(
                selected_dataset=dataset,
                labeling_budget=labeling_budget,
                cell_folds=cell_folds,
                domain_folds=domain_folds,
            )
            st.session_state.sampled_cells = sampled_cells

if st.session_state.run_quality_folding:
    cards: List[Dict[str, Any]] = st.session_state.get("sampled_cells", [])
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
                card_id = cards[idx]["id"]
                key = str(card_id)
                new_val = action == "right"
                if st.session_state.labeling_results.get(key) is None:
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
