import streamlit as st
import pandas as pd
import numpy as np
import time
import os
import json
from backend import backend_pull_errors
from components import render_sidebar, apply_base_styles, render_restart_expander, render_inline_restart_button, get_current_theme
from components.utils import is_pipeline_dirty

# Set the page title and layout
st.set_page_config(page_title="Error Detection", layout="wide")
st.title("Error Detection")

# If pipeline has been modified, inform that shown errors may be from a previous run
# if is_pipeline_dirty():
#     st.info("Pipeline changed earlier in this session. Showing the last saved detected errors until you re-run labeling/propagation.")

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
datasets_path = os.path.join(os.path.dirname(__file__), "../datasets", selected_dataset)

# Get the current theme to extract primary color
current_theme = get_current_theme()
primary_color = current_theme.get('primaryColor', '#f4b11c').strip()

# Convert hex color to RGB values for rgba usage
def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

primary_rgb = hex_to_rgb(primary_color)

# Function to load and display table with propagated errors
def display_table_with_errors(table_name, error_cells):
    file_path = os.path.join(datasets_path, table_name, "clean.csv")
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        st.error(f"Could not load {file_path}: {e}")
        return

    # Define a style function to highlight the error cells with confidence
    def highlight_errors(data):
        df_styles = pd.DataFrame("", index=data.index, columns=data.columns)
        for error in error_cells:
            try:
                confidence = error["confidence"]
                # Convert confidence to opacity (higher confidence = more opaque)
                opacity = confidence
                r, g, b = primary_rgb
                df_styles.iloc[error["row"], data.columns.get_loc(error["col"])] = f"background-color: rgba({r}, {g}, {b}, {opacity}); color: white"
            except Exception:
                continue
        return df_styles

    # Apply styling and display
    styled_df = df.style.apply(highlight_errors, axis=None)
    return styled_df

# Display loading message
with st.spinner("🔍 Searching for possible errors in the datasets..."):
    # Get errors using the new backend function
    results = backend_pull_errors(selected_dataset)
    propagated_errors = results["propagated_errors"]
    
    # Display tables with propagated errors
    st.markdown("### Detected Errors")
    st.markdown("The intensity of the highlighting indicates the confidence level of the error detection (darker = higher confidence)")
    
    for table, errors in propagated_errors.items():
        with st.expander(f"📊 {table} ({len(errors)} potential errors)"):
            styled_df = display_table_with_errors(table, errors)
            if styled_df is not None:
                st.dataframe(styled_df)
                
                # Display error details
                st.markdown("#### Error Details:")
                for error in errors:
                    confidence_percentage = int(error["confidence"] * 100)
                    source = error.get("source", "Unknown")
                    st.markdown(f"""
                    - **Cell**: Row {error['row']}, Column `{error['col']}`
                    - **Value**: `{error['val']}`
                    - **Confidence**: {confidence_percentage}%
                    - **Source**: {source}
                    ---
                    """)

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
