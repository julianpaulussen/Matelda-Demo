import streamlit as st
import pandas as pd
import numpy as np
import time
import os
import json

try:  # Prefer st_aggrid for interactive tables but allow a fallback
    from st_aggrid import (
        AgGrid,
        GridOptionsBuilder,
        GridUpdateMode,
        JsCode,
    )
    AGGRID_AVAILABLE = True
except Exception:  # pragma: no cover - st_aggrid may not be installed
    AGGRID_AVAILABLE = False

from backend import backend_pull_errors
from components import render_sidebar, apply_base_styles

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
datasets_path = os.path.join(os.path.dirname(__file__), "../datasets", selected_dataset)

# Function to load and display table with propagated errors
def display_table_with_errors(table_name, error_cells):
    """Render a table and expose controls to step through detected errors."""
    file_path = os.path.join(datasets_path, table_name, "clean.csv")
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        st.error(f"Could not load {file_path}: {e}")
        return

    idx_key = f"{table_name}_current_error_idx"
    if idx_key not in st.session_state:
        st.session_state[idx_key] = 0

    if not error_cells:
        st.dataframe(df)
        return

    # Build mapping from cell coordinates to color for highlighting
    error_styles = {}
    for err in error_cells:
        try:
            confidence = err["confidence"]
            color_intensity = int(255 * (1 - confidence))
            color = f"rgb(255, {color_intensity}, {color_intensity})"
            error_styles[f"{err['row']}_{err['col']}"] = color
        except Exception:
            continue

    current_idx = st.session_state[idx_key]
    current_idx = max(0, min(current_idx, len(error_cells) - 1))
    st.session_state[idx_key] = current_idx
    current_error = error_cells[current_idx]

    if AGGRID_AVAILABLE:
        # Configure grid with cell styling and scrolling to active error
        active_key = f"{current_error['row']}_{current_error['col']}"
        style_jscode = JsCode(
            f"""
            function(params) {{
                const styles = {json.dumps(error_styles)};
                const key = params.node.rowIndex + '_' + params.colDef.field;
                let style = {{}};
                if(styles[key]) {{
                    style['backgroundColor'] = styles[key];
                    style['color'] = 'white';
                }}
                if(key === '{active_key}') {{
                    style['border'] = '3px solid black';
                }}
                return style;
            }}
            """
        )

        gb = GridOptionsBuilder.from_dataframe(df)
        for col in df.columns:
            gb.configure_column(col, cellStyle=style_jscode)
        gb.configure_selection(selection_mode="single", use_checkbox=False, pre_selected_rows=[current_error["row"]])
        grid_options = gb.build()
        grid_options["enableRangeSelection"] = True
        grid_options["suppressRowClickSelection"] = False
        grid_options["onGridReady"] = JsCode(
            f"""
            function(params) {{
                params.api.setFocusedCell({current_error['row']}, '{current_error['col']}');
                params.api.ensureIndexVisible({current_error['row']}, 'middle');
            }}
            """
        )

        grid_response = AgGrid(
            df,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            allow_unsafe_jscode=True,
        )

        # Update index when user clicks a highlighted cell
        selected = grid_response.get("selected_cells") or []
        if selected:
            cell = selected[0]
            row_idx = cell.get("rowIndex")
            col_id = cell.get("column_id") or cell.get("colId")
            for i, err in enumerate(error_cells):
                if err["row"] == row_idx and err["col"] == col_id:
                    st.session_state[idx_key] = i
                    break
    else:
        # Fallback to standard dataframe rendering
        def highlight_errors(data):
            df_styles = pd.DataFrame("", index=data.index, columns=data.columns)
            for key, color in error_styles.items():
                row, col = key.split("_", 1)
                df_styles.iloc[int(row), data.columns.get_loc(col)] = f"background-color: {color}; color: white"
            return df_styles

        styled_df = df.style.apply(highlight_errors, axis=None)
        st.dataframe(styled_df)

    # Navigation buttons
    prev_col, next_col = st.columns(2)
    with prev_col:
        if st.button("Previous", key=f"{table_name}_prev") and st.session_state[idx_key] > 0:
            st.session_state[idx_key] -= 1
            st.experimental_rerun()
    with next_col:
        if st.button("Next", key=f"{table_name}_next") and st.session_state[idx_key] < len(error_cells) - 1:
            st.session_state[idx_key] += 1
            st.experimental_rerun()

    # Display details for the active error
    current_error = error_cells[st.session_state[idx_key]]
    confidence_percentage = int(current_error["confidence"] * 100)
    source = current_error.get("source", "Unknown")
    st.markdown("#### Error Details:")
    st.markdown(
        f"""
        - **Cell**: Row {current_error['row']}, Column `{current_error['col']}`
        - **Value**: `{current_error['val']}`
        - **Confidence**: {confidence_percentage}%
        - **Source**: {source}
        ---
        """
    )

# Display loading message
with st.spinner("🔍 Searching for possible errors in the datasets..."):
    # Get errors using the new backend function
    results = backend_pull_errors(selected_dataset)
    propagated_errors = results["propagated_errors"]
    
    # Display tables with propagated errors
    st.markdown("### 🔍 Detected Errors")
    st.markdown("The intensity of the red highlighting indicates the confidence level of the error detection (darker = higher confidence)")
    
    for table, errors in propagated_errors.items():
        with st.expander(f"📊 {table} ({len(errors)} potential errors)"):
            display_table_with_errors(table, errors)

# Navigation button to move to the next page
if st.button("Next"):
    st.switch_page("pages/Results.py")
