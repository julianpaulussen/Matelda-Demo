import streamlit as st
import pandas as pd
import numpy as np
import time
import os
import json
from backend import backend_pull_errors
from components import (
    render_sidebar,
    apply_base_styles,
    render_restart_expander,
    render_inline_restart_button,
    render_error_detection_viewer,
)

# Set the page title and layout
st.set_page_config(page_title="Error Detection", layout="wide")
st.title("Error Detection")

# Apply base styles
apply_base_styles()

# Sidebar navigation
render_sidebar()

# ---------------------------------------------------------------------------
# Determine the selected dataset, loading from the pipeline configuration if
# available. Warn the user if no dataset is configured.
# ---------------------------------------------------------------------------
if "dataset_select" not in st.session_state and "pipeline_path" in st.session_state:
    cfg_path = os.path.join(st.session_state.pipeline_path, "configurations.json")
    if os.path.exists(cfg_path):
        with open(cfg_path) as f:
            cfg = json.load(f)
        selected = cfg.get("selected_dataset")
        if selected:
            st.session_state.dataset_select = selected

if "dataset_select" not in st.session_state:
    st.warning("⚠️ Dataset not configured.")
    if st.button("Go back to Configurations"):
        st.switch_page("pages/Configurations.py")
    st.stop()

selected_dataset = st.session_state.dataset_select

# Display loading message
with st.spinner("🔍 Searching for possible errors in the datasets..."):
    results = backend_pull_errors(selected_dataset)
    propagated_errors = results.get("propagated_errors", {})

    # Use the new component with lazy-loading + navigator
    render_error_detection_viewer(selected_dataset, propagated_errors)

st.markdown("---")
nav_cols = st.columns([1, 1, 1], gap="small")

# Restart: confirmation dialog to go to app.py
with nav_cols[0]:
    render_inline_restart_button(page_id="error_detection", use_container_width=True)

# Back: to Propagated Errors
if nav_cols[1].button("Back", key="err_back", use_container_width=True):
    st.switch_page("pages/PropagatedErrors.py")

# Next: to Results
if nav_cols[2].button("Next", key="err_next", use_container_width=True):
    st.switch_page("pages/Results.py")
