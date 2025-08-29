import os
import json
import requests
import streamlit as st
from typing import Dict, Any, List
from streamlit_swipecards import streamlit_swipecards
from components import (
    render_sidebar,
    apply_base_styles,
    get_current_theme,
    get_datasets_path,
    get_swipecard_colors,
)
from components.utils import mark_pipeline_dirty
from backend.api import ensure_api_started

st.set_page_config(page_title="Player Labeling", layout="wide")
apply_base_styles(get_current_theme())
render_sidebar()

API_BASE = ensure_api_started()

sid = st.session_state.get("mp.session_id")
pid = st.session_state.get("mp.player_id")
name = st.session_state.get("mp.display_name")
if not sid or not pid:
    st.warning("No active session. Go back to Join.")
    st.page_link("pages/03_Multi_Join.py", label="← Back to Join")
    st.stop()

st.title("Labeling")
st.caption(f"Player: {name}")

API_TIMEOUT = 10

def fetch_batch():
    try:
        r = requests.get(f"{API_BASE}/sessions/{sid}/players/{pid}/next-batch", timeout=API_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Failed to load assignment: {e}")
        return {"items": [], "last_index": 0}

def fetch_status():
    try:
        r = requests.get(f"{API_BASE}/sessions/{sid}", timeout=API_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {"status": "unknown"}

# Initialize assigned items once; reuse single-player session_state keys
if "sampled_cells" not in st.session_state:
    # Wait until session becomes active if needed
    meta = fetch_status()
    if meta.get("status") in {"lobby", "preparing", None}:
        try:
            from streamlit_autorefresh import st_autorefresh
            st.info("Waiting for host to prepare sampling…")
            st_autorefresh(interval=3000, key="player_wait_refresh")
        except Exception:
            st.info("Waiting for host to prepare sampling… Click Refresh.")
            if st.button("Refresh"):
                st.rerun()
        st.stop()
    batch = fetch_batch()
    items = batch.get("items", [])
    if not items:
        st.info("No items assigned yet. Try Refresh in a moment.")
        if st.button("Refresh"):
            st.rerun()
        st.stop()
    # Set dataset for table-mode rendering (comes from backend items)
    ds = items[0].get("selected_dataset") or items[0].get("dataset")
    if ds:
        st.session_state.dataset_select = ds
    st.session_state.sampled_cells = items

dataset = st.session_state.get("dataset_select")
cards: List[Dict[str, Any]] = st.session_state.get("sampled_cells", [])

def make_card(cell: Dict[str, Any]) -> Dict[str, Any]:
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

card_data = [c for c in (make_card(card) for card in cards) if c]

st.info("Swipe left to mark as error, swipe right to mark as correct.")

results = streamlit_swipecards(
    cards=card_data,
    display_mode="table",
    view="desktop",
    key="labeling_cards",
    last_card_message="No more cards to swipe, continue with the Next-button below.",
    colors=get_swipecard_colors(),
)

if "labeling_results" not in st.session_state:
    st.session_state.labeling_results = {}

# Record swipes like single-player and also POST to backend for persistence
if results and isinstance(results.get("swipedCards", None), list):
    swipes = results.get("swipedCards", [])
    made_changes = False
    for swipe in swipes:
        idx = swipe.get("index")
        action = swipe.get("action")
        if idx is not None and action in {"left", "right"} and idx < len(cards):
            card_id = cards[idx].get("id") or cards[idx].get("sample_id")
            key = str(card_id)
            new_val = action == "right"  # True == correct
            if st.session_state.labeling_results.get(key) is None:
                st.session_state.labeling_results[key] = new_val
                # Submit incrementally to backend
                try:
                    label_value = "correct" if new_val else "error"
                    payload = [{
                        "item_id": card_id,
                        "label_value": label_value,
                        "order_index": int(idx),
                    }]
                    requests.post(
                        f"{API_BASE}/sessions/{sid}/players/{pid}/labels",
                        json=payload,
                        timeout=API_TIMEOUT,
                    )
                except Exception:
                    # Non-blocking
                    pass
                made_changes = True
    if made_changes:
        mark_pipeline_dirty()

st.markdown("---")
nav_cols = st.columns([1, 1, 1], gap="small")

with nav_cols[0]:
    from components import render_inline_restart_button
    render_inline_restart_button(page_id="labeling", use_container_width=True)

if nav_cols[1].button("Back", key="player_label_back", use_container_width=True):
    # Keep host in host flow; players go back to lobby
    if st.session_state.get("mp.role") == "host":
        st.switch_page("pages/07_Multi_HostProgress.py")
    else:
        st.switch_page("pages/04_Multi_PlayerLobby.py")

if nav_cols[2].button("Next", key="player_label_next", use_container_width=True):
    # If all items labeled, host proceeds to Propagated Errors; players to Thanks
    done = sum(1 for c in cards if str((c.get("id") or c.get("sample_id"))) in st.session_state.labeling_results)
    if done >= len(cards):
        if st.session_state.get("mp.role") == "host":
            # After host finishes, go to host progress lobby
            st.switch_page("pages/07_Multi_HostProgress.py")
        else:
            st.switch_page("pages/06_Multi_PlayerThanks.py")
    else:
        st.info("Please finish labeling all assigned items.")
