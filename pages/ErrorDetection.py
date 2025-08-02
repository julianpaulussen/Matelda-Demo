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
    import streamlit.components.v1 as components

    def basic_aggrid(df, error_styles=None, current_error=None, height=400):
        """Render a minimal AG Grid via a custom Streamlit component."""
        row_data = df.to_dict(orient="records")
        column_defs = [{"field": c} for c in df.columns]
        error_styles = error_styles or {}
        active_key = (
            f"{current_error['row']}_{current_error['col']}"
            if current_error is not None
            else ""
        )
        html = f"""
<link rel=\"stylesheet\" href=\"https://unpkg.com/ag-grid-community/dist/styles/ag-grid.css\">
<link rel=\"stylesheet\" href=\"https://unpkg.com/ag-grid-community/dist/styles/ag-theme-alpine.css\">
<style>
    .ag-theme-alpine {{
        --ag-background-color: #ffffff;
        --ag-header-background-color: #f8f9fa;
        --ag-odd-row-background-color: #ffffff;
        --ag-even-row-background-color: #f8f9fa;
        --ag-border-color: #dee2e6;
        --ag-cell-horizontal-border: solid #dee2e6;
        --ag-header-column-separator-color: #dee2e6;
        --ag-font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
        --ag-font-size: 14px;
        --ag-row-height: 42px;
        --ag-header-height: 48px;
        transition: all 0.3s ease-in-out;
    }}
    .ag-cell {{
        line-height: 42px;
        padding: 0 12px;
        transition: all 0.3s ease-in-out;
    }}
    .ag-header-cell {{
        font-weight: 600;
        padding: 0 12px;
    }}
    .ag-cell.highlight-transition {{
        transition: background-color 0.5s ease-in-out, border 0.5s ease-in-out, transform 0.3s ease-in-out;
    }}
    .ag-cell.active-error {{
        animation: pulseHighlight 1s ease-in-out;
        transform: scale(1.02);
    }}
    @keyframes pulseHighlight {{
        0% {{ transform: scale(1); }}
        50% {{ transform: scale(1.05); }}
        100% {{ transform: scale(1.02); }}
    }}
</style>
<div id=\"grid\" class=\"ag-theme-alpine\" style=\"width:100%;height:{height}px;\"></div>
<script src=\"https://unpkg.com/ag-grid-community/dist/ag-grid-community.min.noStyle.js\"></script>
<script>
    const rowData = {json.dumps(row_data)};
    const columnDefs = {json.dumps(column_defs)};
    const errorStyles = {json.dumps(error_styles)};
    const activeKey = '{active_key}';
    
    const gridOptions = {{
        columnDefs: columnDefs,
        rowData: rowData,
        animateRows: true,
        onGridReady: params => {{
            window.currentGridApi = params.api;
            if(activeKey) {{
                const [row, col] = activeKey.split('_');
                // Smooth scroll to the active error
                setTimeout(() => {{
                    params.api.ensureIndexVisible(Number(row), 'middle');
                    params.api.setFocusedCell(Number(row), col);
                    
                    // Add highlight animation
                    setTimeout(() => {{
                        const selector = `[row-index="${{row}}"] [col-id="${{col}}"]`;
                        const cell = document.querySelector(selector);
                        if (cell) {{
                            cell.classList.add('active-error');
                            cell.scrollIntoView({{
                                behavior: 'smooth',
                                block: 'center',
                                inline: 'center'
                            }});
                        }}
                    }}, 150);
                }}, 200);
            }}
        }},
        onCellClicked: event => {{
            const key = event.rowIndex + '_' + event.colDef.field;
            Streamlit.setComponentValue(key);
        }},
        getCellStyle: params => {{
            const key = params.rowIndex + '_' + params.colDef.field;
            let style = {{}};
            if(errorStyles[key]) {{
                style.backgroundColor = errorStyles[key];
                style.color = 'white';
                style.fontWeight = 'bold';
            }}
            if(key === activeKey) {{
                style.border = '3px solid #1f77b4';
                style.borderRadius = '4px';
                style.boxShadow = '0 0 10px rgba(31, 119, 180, 0.5)';
            }}
            return style;
        }}
    }};
    new agGrid.Grid(document.getElementById('grid'), gridOptions);
</script>
        """
        return components.html(html, height=height)

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
@st.cache_data
def load_table_data(file_path):
    """Load and cache table data."""
    try:
        return pd.read_csv(file_path)
    except Exception as e:
        st.error(f"Could not load {file_path}: {e}")
        return None

def display_table_with_errors(table_name, error_cells):
    """Render a table and expose controls to step through detected errors."""
    file_path = os.path.join(datasets_path, table_name, "clean.csv")
    
    # Use cached data loading
    df = load_table_data(file_path)
    if df is None:
        return

    idx_key = f"{table_name}_current_error_idx"
    if idx_key not in st.session_state:
        st.session_state[idx_key] = 0

    if not error_cells and AGGRID_AVAILABLE:
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_selection(selection_mode="single", use_checkbox=False)
        grid_options = gb.build()
        AgGrid(
            df,
            gridOptions=grid_options,
            theme="streamlit",
            fit_columns_on_grid_load=True,
        )
        return
    elif not error_cells:
        basic_aggrid(df)
        return

    # Build mapping from cell coordinates to color for highlighting (cached)
    cache_key = f"{table_name}_error_styles"
    if cache_key not in st.session_state:
        error_styles = {}
        for err in error_cells:
            try:
                confidence = err["confidence"]
                color_intensity = int(255 * (1 - confidence))
                color = f"rgb(255, {color_intensity}, {color_intensity})"
                error_styles[f"{err['row']}_{err['col']}"] = color
            except Exception:
                continue
        st.session_state[cache_key] = error_styles
    else:
        error_styles = st.session_state[cache_key]

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
                    style['fontWeight'] = 'bold';
                }}
                if(key === '{active_key}') {{
                    style['border'] = '3px solid #1f77b4';
                    style['borderRadius'] = '4px';
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
        grid_options["animateRows"] = True
        grid_options["rowSelection"] = "single"
        grid_options["suppressCellSelection"] = False
        grid_options["onGridReady"] = JsCode(
            f"""
            function(params) {{
                window.gridApi = params.api;
                window.gridColumnApi = params.columnApi;
                
                // Function to smoothly navigate to error
                window.navigateToError = function(row, col) {{
                    // Clear previous highlights
                    document.querySelectorAll('.ag-cell.active-error').forEach(cell => {{
                        cell.classList.remove('active-error');
                    }});
                    
                    // Smooth scroll to new position
                    params.api.ensureIndexVisible(row, 'middle');
                    params.api.setFocusedCell(row, col);
                    
                    setTimeout(() => {{
                        const selector = `[row-index="${{row}}"] [col-id="${{col}}"]`;
                        const cell = document.querySelector(selector);
                        if (cell) {{
                            cell.classList.add('active-error');
                            cell.scrollIntoView({{
                                behavior: 'smooth',
                                block: 'center',
                                inline: 'center'
                            }});
                        }}
                    }}, 100);
                }};
                
                // Initial navigation to current error
                const row = {current_error['row']};
                const col = '{current_error['col']}';
                setTimeout(() => window.navigateToError(row, col), 200);
            }}
            """
        )

        # Create a container for the grid that persists
        grid_container = st.container()
        
        with grid_container:
            grid_response = AgGrid(
                df,
                gridOptions=grid_options,
                update_mode=GridUpdateMode.SELECTION_CHANGED,
                allow_unsafe_jscode=True,
                theme="streamlit",
                fit_columns_on_grid_load=True,
                key=f"{table_name}_grid_stable",  # Use stable key
                custom_css={
                    ".ag-theme-streamlit": {
                        "font-family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif",
                        "font-size": "14px"
                    },
                    ".ag-cell": {
                        "line-height": "42px",
                        "padding": "0 12px",
                        "transition": "all 0.3s ease-in-out"
                    },
                    ".ag-header-cell": {
                        "font-weight": "600",
                        "padding": "0 12px"
                    },
                    ".ag-cell.active-error": {
                        "animation": "pulseHighlight 1s ease-in-out",
                        "transform": "scale(1.02)"
                    },
                    "@keyframes pulseHighlight": {
                        "0%": {"transform": "scale(1)"},
                        "50%": {"transform": "scale(1.05)"},
                        "100%": {"transform": "scale(1.02)"}
                    }
                }
            )

        # Update index when user clicks a highlighted cell
        selected_cells = grid_response.get("selected_cells")
        selected_rows = grid_response.get("selected_rows")
        
        # Handle selected cells
        if selected_cells is not None and len(selected_cells) > 0:
            cell = selected_cells[0]
            row_idx = cell.get("rowIndex")
            col_id = cell.get("column_id") or cell.get("colId")
            for i, err in enumerate(error_cells):
                if err["row"] == row_idx and err["col"] == col_id:
                    if st.session_state[idx_key] != i:
                        st.session_state[idx_key] = i
                        st.rerun()
                    break
        
        # Handle selected rows (fallback) - fix DataFrame indexing issue
        elif selected_rows is not None and not selected_rows.empty:
            try:
                # Get the first row from the DataFrame
                row_data = selected_rows.iloc[0]
                if hasattr(row_data, 'name'):  # row_data is a Series with an index
                    row_idx = row_data.name
                    # Find any error in this row and select it
                    for i, err in enumerate(error_cells):
                        if err["row"] == row_idx:
                            if st.session_state[idx_key] != i:
                                st.session_state[idx_key] = i
                                st.rerun()
                            break
            except Exception:
                pass  # Ignore errors in row selection handling
    else:
        # Use a stable container for basic aggrid
        with st.container():
            basic_aggrid(df, error_styles, current_error)

    # Navigation controls with error counter
    nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
    
    with nav_col1:
        if st.button("Previous", key=f"{table_name}_prev", disabled=st.session_state[idx_key] == 0):
            st.session_state[idx_key] -= 1
            st.rerun()
    
    with nav_col2:
        st.markdown(f"<div style='text-align: center; padding: 8px;'><strong>Error {st.session_state[idx_key] + 1} of {len(error_cells)}</strong></div>", unsafe_allow_html=True)
    
    with nav_col3:
        if st.button("Next", key=f"{table_name}_next", disabled=st.session_state[idx_key] == len(error_cells) - 1):
            st.session_state[idx_key] += 1
            st.rerun()

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
    
    for i, (table, errors) in enumerate(propagated_errors.items()):
        # Expand the first table with errors by default
        expanded = i == 0 and len(errors) > 0
        with st.expander(f"📊 {table} ({len(errors)} potential errors)", expanded=expanded):
            display_table_with_errors(table, errors)

# Navigation button to move to the next page
if st.button("Next"):
    st.switch_page("pages/Results.py")
