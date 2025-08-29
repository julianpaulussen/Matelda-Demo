import os
import json
import requests
import streamlit as st
from components import render_sidebar, apply_base_styles, get_current_theme
from components.session_persistence import persist_session
from components.utils import get_datasets_path
from streamlit_swipecards import streamlit_swipecards

st.set_page_config(page_title="Labeling", layout="wide")
apply_base_styles(get_current_theme())
render_sidebar()


def api_base() -> str:
    return os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")


st.title("Labeling")

sid = st.session_state.get("mp.session_id")
pid = st.session_state.get("mp.player_id")
name = st.session_state.get("mp.display_name")

if not (sid and pid):
    st.warning("No session joined. Go to Join page.")
    st.stop()

st.info(f"Player: {name}")

try:
    batch = requests.get(
        f"{api_base()}/api/sessions/{sid}/players/{pid}/next-batch", timeout=10
    ).json().get("items", [])
except Exception as e:
    st.error(f"Failed to fetch batch: {e}")
    batch = []

if not batch:
    st.info("No items assigned yet. If the host just started, try Refresh.")
    if st.button("Refresh"):
        st.rerun()
    st.stop()

def make_card_from_payload(dataset: str, payload_json: str):
    try:
        p = json.loads(payload_json)
        datasets_path = get_datasets_path(dataset)
        dataset_path = os.path.join(datasets_path, p["table"], "clean.csv")
        row = int(p.get("row", 0))
        column = p.get("col", "")
        return {
            "dataset_path": dataset_path,
            "row_index": row,
            "name": f"{p.get('table','')}:{row}:{column}",
            "description": f"Value: {p.get('val','')}",
            "highlight_cells": [{"row": row, "column": column}],
            "highlight_rows": [{"row": row}],
            "highlight_columns": [{"column": column}],
            "center_table_row": row,
            "center_table_column": column,
        }
    except Exception:
        return None

if "mp.swipes" not in st.session_state:
    st.session_state["mp.swipes"] = {}

# Always pass the full batch to preserve widget internal position across reruns
card_data = []
index_to_item_id = {}
for idx, it in enumerate(batch):
    payload = json.dumps({
        "dataset": it.get("dataset"),
        "table": it.get("table"),
        "row": it.get("row"),
        "col": it.get("col"),
        "val": it.get("val"),
    })
    card = make_card_from_payload(it.get("dataset"), payload)
    if card:
        index_to_item_id[len(card_data)] = it.get("sample_id")
        card_data.append(card)

results = streamlit_swipecards(
    cards=card_data,
    display_mode="table",
    view="desktop",
    key="mp_labeling_cards",
    last_card_message="No more cards to swipe, press Next.",
)

def _extract_swipes(res):
    if not res:
        return []
    if isinstance(res.get("swipedCards"), list):
        return res.get("swipedCards", [])
    if res.get("lastSwipe"):
        return [res.get("lastSwipe")]
    return []

# Persist newly swiped items and immediately sync to backend (UPSERT)
newly = []
for swipe in _extract_swipes(results):
    idx = swipe.get("index")
    action = swipe.get("action")
    if idx is None or action not in {"left", "right"}:
        continue
    item_id = index_to_item_id.get(idx)
    if item_id is None:
        continue
    val = True if action == "right" else False
    prev = st.session_state["mp.swipes"].get(item_id)
    st.session_state["mp.swipes"][item_id] = val
    if prev is None or prev != val:
        newly.append({"item_id": item_id, "label_value": "true" if val else "false"})

if newly:
    try:
        requests.post(
            f"{api_base()}/api/sessions/{sid}/players/{pid}/labels",
            json=newly,
            timeout=10,
        )
    except Exception:
        pass
    # Persist to session storage too
    persist_session()

done_count = len(st.session_state["mp.swipes"]) if st.session_state.get("mp.swipes") else 0
st.caption(f"Progress: {done_count}/{len(batch)} labeled")

if st.button("Next", type="primary"):
    to_send = [
        {"item_id": k, "label_value": "true" if v else "false"}
        for k, v in st.session_state.get("mp.swipes", {}).items()
    ]
    if not to_send:
        st.warning("No swipes captured yet. Please swipe some cards.")
        st.stop()
    try:
        requests.post(
            f"{api_base()}/api/sessions/{sid}/players/{pid}/labels", json=to_send, timeout=20
        )
        if st.session_state.get("mp.role") == "host":
            st.switch_page("pages/07_Multi_HostProgress.py")
        else:
            st.switch_page("pages/06_Multi_PlayerThanks.py")
    except Exception as e:
        st.error(f"Failed to submit labels: {e}")
