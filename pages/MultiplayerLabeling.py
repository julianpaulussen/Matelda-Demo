import os
import json
from typing import Dict, Any, List

import streamlit as st
from streamlit_swipecards import streamlit_swipecards

from components import render_sidebar, apply_base_styles, get_datasets_path
from backend.multiplayer import (
    get_session,
    submit_player_labels,
)

st.set_page_config(page_title="Multiplayer Labeling", layout="wide")
st.title("Labeling (Multiplayer)")
apply_base_styles()
render_sidebar()


def make_card(cell: Dict[str, Any], dataset: str) -> Dict[str, Any]:
    datasets_path = get_datasets_path(dataset)
    dataset_path = os.path.join(datasets_path, cell.get("table"), "clean.csv")
    row = int(cell.get("row", 0))
    column = cell.get("col", "")
    return {
        "dataset_path": dataset_path,
        "row_index": row,
        "name": cell.get("name", f"{cell.get('table')}"),
        "description": f"Value: {cell.get('val', '')}",
        "highlight_cells": [{"row": row, "column": column}],
        "highlight_rows": [{"row": row}],
        "highlight_columns": [{"column": column}],
        "center_table_row": row,
        "center_table_column": column,
    }


query = st.query_params
session_id = query.get("session") if isinstance(query.get("session"), str) else (query.get("session")[0] if query.get("session") else None)
player_id = query.get("player") if isinstance(query.get("player"), str) else (query.get("player")[0] if query.get("player") else None)

if not (session_id and player_id):
    st.error("Missing session or player information.")
    st.stop()

pipeline_path = st.session_state.get("pipeline_path")
if not pipeline_path:
    st.error("No pipeline selected.")
    st.stop()

sess = get_session(pipeline_path, session_id)
if not sess:
    st.error("Session not found.")
    st.stop()

dataset = sess.get("dataset")
player = sess.get("players", {}).get(player_id)
if not player:
    st.error("Player not found in session.")
    st.stop()

cards: List[Dict[str, Any]] = player.get("assigned", [])
if not cards:
    st.info("No assigned items yet. If you just joined, wait for the host to start.")
    st.stop()

card_data = [make_card(c, dataset) for c in cards]
st.info("Swipe left to mark as error, swipe right to mark as correct.")
results = streamlit_swipecards(cards=card_data, display_mode="table", key=f"mp_cards_{player_id}")

if "mp_labeling_results" not in st.session_state:
    st.session_state.mp_labeling_results = {}

if results and results.get("swipedCards"):
    for swipe in results.get("swipedCards", []):
        idx = swipe.get("index")
        action = swipe.get("action")
        if idx is not None and action in {"left", "right"} and idx < len(cards):
            card_id = idx  # local index, unique within assignment
            st.session_state.mp_labeling_results[str(card_id)] = action == "right"

st.markdown("---")
cols = st.columns([1, 1])
if cols[0].button("Back to Multiplayer", use_container_width=True):
    st.switch_page("pages/Multiplayer.py")

if cols[1].button("Next", type="primary", use_container_width=True):
    labeled_cells = []
    for i, cell in enumerate(cards):
        is_correct = st.session_state.mp_labeling_results.get(str(i), False)
        labeled_cells.append(
            {
                "table": cell.get("table"),
                "row": cell.get("row", 0),
                "col": cell.get("col", ""),
                "val": cell.get("val", ""),
                "domain_fold": cell.get("domain_fold", ""),
                "cell_fold": cell.get("cell_fold", ""),
                "cell_fold_label": cell.get("cell_fold_label", "neutral"),
                "is_error": not is_correct,
            }
        )
    submit_player_labels(pipeline_path, session_id, player_id, labeled_cells)
    # Host goes to progress page, player sees thank you page
    if player.get("is_host"):
        st.query_params["session"] = session_id
        st.switch_page("pages/HostProgress.py")
    else:
        st.switch_page("pages/PlayerDone.py")

