import streamlit as st
import time
import json
import os
from typing import Dict, Any, List

from streamlit_swipecards import streamlit_swipecards

from backend import backend_sample_labeling, backend_label_propagation

# Hide default Streamlit menu
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] {display: none;}
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.page_link("app.py", label="Matelda")
    st.page_link("pages/Configurations.py", label="Configurations")
    st.page_link("pages/DomainBasedFolding.py", label="Domain Based Folding")
    st.page_link("pages/QualityBasedFolding.py", label="Quality Based Folding")
    st.page_link("pages/Labeling.py", label="Labeling")
    st.page_link("pages/PropagatedErrors.py", label="Propagated Errors")
    st.page_link("pages/ErrorDetection.py", label="Error Detection")
    st.page_link("pages/Results.py", label="Results")


def make_card(cell: Dict[str, Any]) -> Dict[str, Any]:
    """Create a card dictionary for streamlit-swipecards in table mode."""

    dataset = st.session_state.get("dataset_select")
    dataset_path = os.path.join("datasets", dataset, cell["table"], "clean.csv")

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
        "key": str(cell.get("id")),
    }


if "run_quality_folding" not in st.session_state:
    st.session_state.run_quality_folding = False

st.title("Labeling")

if not st.session_state.run_quality_folding:
    if st.button("Run Labeling"):
        with st.spinner("🔄 Processing... Please wait..."):
            selected_dataset = st.session_state.get("dataset_select")
            labeling_budget = st.session_state.get("labeling_budget", 10)
            cell_folds = st.session_state.get("cell_folds", {})
            domain_folds = st.session_state.get("domain_folds", {})
            sampled_cells = backend_sample_labeling(
                selected_dataset=selected_dataset,
                labeling_budget=labeling_budget,
                cell_folds=cell_folds,
                domain_folds=domain_folds,
            )
            st.session_state.sampled_cells = sampled_cells
            time.sleep(2)
        st.session_state.run_quality_folding = True
        st.rerun()

if st.session_state.run_quality_folding:
    cards: List[Dict[str, Any]] = st.session_state.get("sampled_cells", [])
    card_data = [make_card(card) for card in cards]

    st.info(
        "Swipe left to mark as error, swipe right to mark as correct.")

    results = streamlit_swipecards(card_data, display_mode="table", key="labeling_cards")

    if "labeling_results" not in st.session_state:
        st.session_state.labeling_results = {}

    if results and results.get("swipedCards"):
        for swipe in results.get("swipedCards", []):
            idx = swipe.get("index")
            action = swipe.get("action")
            if idx is not None and action in {"left", "right"} and idx < len(cards):
                card_id = cards[idx]["id"]
                st.session_state.labeling_results[str(card_id)] = action == "right"

    st.markdown("---")

    if st.button("Next"):
        labeled_cells = []
        for cell in cards:
            is_error = not st.session_state.labeling_results.get(str(cell["id"]), False)
            cell_info = {
                "table": cell.get("table"),
                "is_error": is_error,
                "row": cell.get("row", 0),
                "col": cell.get("col", ""),
                "val": cell.get("val", ""),
                "domain_fold": cell.get("domain_fold", ""),
                "cell_fold": cell.get("cell_fold", ""),
            }
            labeled_cells.append(cell_info)

        selected_dataset = st.session_state.get("dataset_select")
        propagation_results = backend_label_propagation(selected_dataset, labeled_cells)
        st.session_state.propagation_results = propagation_results
        st.session_state.propagation_saved = False
        st.switch_page("pages/PropagatedErrors.py")
