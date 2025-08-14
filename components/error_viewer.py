"""
Reusable Error Detection viewer component with ag-Grid and error navigator.

Public API:
- render_error_detection_viewer(selected_dataset: str, propagated_errors: Dict[str, List[Dict]]):
    Renders a list of tables with lazy-loaded ag-Grid and an error navigator.

Notes:
- Prefers st-aggrid for smooth navigation and styling. If not available,
  falls back to a pure-HTML table (non-Streamlit table) with CSS highlights.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from html import escape

import os
import pandas as pd
import streamlit as st

from .utils import get_datasets_path


def _load_table_df(selected_dataset: str, table_name: str) -> pd.DataFrame:
    datasets_path = get_datasets_path(selected_dataset)
    file_path = os.path.join(datasets_path, table_name, "clean.csv")
    try:
        return pd.read_csv(file_path)
    except Exception as e:
        return pd.DataFrame({"Error": [f"Could not load {file_path}: {e}"]})


def _ensure_css_once() -> None:
    if st.session_state.get("_error_viewer_css_injected"):
        return
    st.session_state["_error_viewer_css_injected"] = True
    st.markdown(
        """
        <style>
        /* Toolbar layout */
        .edv-toolbar { display: grid; grid-template-columns: 1fr auto auto; gap: 8px; align-items: center; margin: 6px 0 10px 0; }
        .edv-toolbar .edv-readonly { border: 1px solid #e6e6e6; border-radius: 10px; padding: 8px 10px; background: #fbfbfd; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; box-shadow: 0 1px 2px rgba(0,0,0,0.04) inset; }
        .edv-toolbar .edv-btn { padding: 6px 10px; border-radius: 6px; border: 1px solid #ddd; background: white; cursor: pointer; }
        .edv-toolbar .edv-btn:disabled { opacity: 0.4; cursor: default; }

        /* Error cell styling and animations */
        .ag-theme-streamlit .error-cell { transition: background-color 240ms ease-in-out, transform 160ms ease-out; }
        .ag-theme-streamlit .current-error-cell { animation: edv-pulse 480ms ease-in-out; transform: translateZ(0); }
        @keyframes edv-pulse { 0% { box-shadow: 0 0 0 0 rgba(255,77,77,0.45); } 100% { box-shadow: 0 0 0 12px rgba(255,77,77,0); } }

        /* Limit grid area and enable scroll */
        .edv-grid-frame { max-width: 1100px; border-radius: 12px; overflow: hidden; border: 1px solid #ececf1; box-shadow: 0 6px 18px rgba(0,0,0,0.06); background: white; }
        .edv-grid-frame .ag-root-wrapper, .edv-grid-frame .ag-theme-streamlit { height: 60vh !important; max-height: 60vh !important; }
        .edv-grid-frame .ag-body-viewport { overflow: auto !important; -webkit-overflow-scrolling: touch; }
        .edv-grid-frame .ag-header { background: #fafbff; border-bottom: 1px solid #ececf1; }
        .edv-grid-frame .ag-row-odd { background: #fcfdff; }
        .edv-grid-frame .ag-row-hover { background: #f3f6ff !important; }

        /* Fallback HTML table theme */
        .edv-table { overflow: auto; max-height: 60vh; max-width: 1100px; border: 1px solid #ececf1; border-radius: 12px; box-shadow: 0 6px 18px rgba(0,0,0,0.06); }
        .edv-table table { border-collapse: collapse; width: 100%; font-size: 13px; }
        .edv-table th, .edv-table td { border: 1px solid #f0f0f5; padding: 8px 10px; }
        .edv-table thead th { position: sticky; top: 0; background: #fafbff; z-index: 2; }
        .edv-table tbody tr:nth-child(odd) { background: #fcfdff; }
        .edv-table tbody tr:hover { background: #f3f6ff; }
        .edv-table td.error-cell { transition: background-color 240ms ease-in-out, transform 160ms ease-out; }
        .edv-table td.current-error-cell { animation: edv-pulse 480ms ease-in-out; }

        /* Subtle slide animation for the toolbar value */
        .edv-readonly.edv-anim { animation: edv-slide 160ms ease-out; }
        @keyframes edv-slide { from { transform: translateY(-4px); opacity: 0.7; } to { transform: translateY(0); opacity: 1; } }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_toolbar(table_key: str, errors: List[Dict[str, Any]]) -> int:
    """Render the navigator toolbar and update/return current error index for this table.

    Stores state under keys derived from `table_key`.
    """
    if not errors:
        st.info("No errors detected for this table.")
        return 0

    idx_key = f"{table_key}__curr_idx"
    curr_idx = st.session_state.get(idx_key, 0)
    curr_idx = max(0, min(curr_idx, len(errors) - 1))
    curr = errors[curr_idx]

    value_name = str(curr.get("val", "")) if curr.get("val") is not None else f"{curr.get('col', '?')}"
    conf_pct = int(round(float(curr.get("confidence", 0)) * 100))
    source = curr.get("source", "Unknown")

    cols = st.columns([6, 1, 1])
    with cols[0]:
        st.markdown(
            f"<div class='edv-toolbar'><div class='edv-readonly edv-anim'>{value_name}</div></div>",
            unsafe_allow_html=True,
        )
    with cols[1]:
        if st.button("⟨", key=f"{table_key}__prev", use_container_width=True, disabled=(curr_idx <= 0)):
            curr_idx = max(0, curr_idx - 1)
    with cols[2]:
        if st.button("⟩", key=f"{table_key}__next", use_container_width=True, disabled=(curr_idx >= len(errors) - 1)):
            curr_idx = min(len(errors) - 1, curr_idx + 1)

    st.session_state[idx_key] = curr_idx
    st.caption(f"Confidence: {conf_pct}%  •  Source: {source}")
    return curr_idx


def _try_import_aggrid():
    try:
        # Lazy import so the app works without it, too
        from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
        return AgGrid, GridOptionsBuilder, JsCode
    except Exception:
        return None, None, None


def _build_error_maps(errors: List[Dict[str, Any]]) -> Dict[str, Dict[int, float]]:
    """Return mapping {col -> {row_index -> confidence}} for quick checks in JS/HTML."""
    col_map: Dict[str, Dict[int, float]] = {}
    for e in errors:
        try:
            col = str(e.get("col"))
            row = int(e.get("row"))
            conf = float(e.get("confidence", 0.0))
            if col not in col_map:
                col_map[col] = {}
            col_map[col][row] = conf
        except Exception:
            continue
    return col_map


def _render_aggrid(df: pd.DataFrame, errors: List[Dict[str, Any]], curr_idx: int, table_key: str) -> None:
    AgGrid, GridOptionsBuilder, JsCode = _try_import_aggrid()
    if not AgGrid:
        _render_html_table(df, errors, curr_idx)
        return

    error_map = _build_error_maps(errors)
    current = errors[curr_idx] if errors else None
    curr_row = int(current.get("row")) if current and current.get("row") is not None else None
    curr_col = str(current.get("col")) if current and current.get("col") is not None else None

    gob = GridOptionsBuilder.from_dataframe(df)

    # Provide context with error map for JS cellClassRules
    grid_context = {"errorMap": error_map, "currRow": curr_row, "currCol": curr_col}

    # Configure columns with class rules and dynamic styles by confidence
    cell_class_js = JsCode(
        """
        function(params) {
            const colId = params.column.getColId();
            const rowIndex = params.node.rowIndex;
            const emap = params.context && params.context.errorMap ? params.context.errorMap : {};
            const isError = (emap[colId] && emap[colId][rowIndex] !== undefined);
            const isCurrent = isError && params.context && params.context.currRow === rowIndex && params.context.currCol === colId;
            if (isCurrent) { return 'current-error-cell'; }
            if (isError) { return 'error-cell'; }
            return null;
        }
        """
    )

    cell_style_js = JsCode(
        """
        function(params){
            const colId = params.column.getColId();
            const rowIndex = params.node.rowIndex;
            const emap = params.context && params.context.errorMap ? params.context.errorMap : {};
            const conf = emap[colId] && emap[colId][rowIndex] !== undefined ? parseFloat(emap[colId][rowIndex]) : null;
            if (conf === null) return null;
            const isCurrent = (params.context && params.context.currRow === rowIndex && params.context.currCol === colId);
            // Map confidence to intensity: base 0.18 .. 0.45
            const base = 0.18, max = 0.45;
            const alpha = base + (max - base) * conf;
            const bg = `rgba(255,77,77,${isCurrent ? Math.min(0.6, alpha + 0.1) : alpha})`;
            return { backgroundColor: bg };
        }
        """
    )

    for c in df.columns:
        gob.configure_column(c, cellClass=cell_class_js, cellStyle=cell_style_js)

    gob.configure_grid_options(
        domLayout="normal",
        ensureDomOrder=True,
        suppressCellFocus=True,
        rowHeight=32,
        context=grid_context,
        onGridReady=JsCode(
            """
            function(params){
                const ctx = params.api.gridOptionsWrapper.gridOptions.context || {};
                if (ctx.currRow != null){
                    setTimeout(function(){
                        try{
                            params.api.ensureIndexVisible(ctx.currRow, 'middle');
                            if (ctx.currCol){ params.api.ensureColumnVisible(ctx.currCol); }
                            const rn = params.api.getDisplayedRowAtIndex(ctx.currRow);
                            if (rn){ params.api.flashCells({ rowNodes: [rn], columns: ctx.currCol ? [ctx.currCol] : undefined, flashDelay: 180, fadeDelay: 420}); }
                        }catch(e){ /* no-op */ }
                    }, 0);
                }
            }
            """
        ),
        onFirstDataRendered=JsCode(
            """
            function(params){
                const ctx = params.api.gridOptionsWrapper.gridOptions.context || {};
                if (ctx.currRow != null){
                    try{
                        params.api.ensureIndexVisible(ctx.currRow, 'middle');
                        if (ctx.currCol){ params.api.ensureColumnVisible(ctx.currCol); }
                    }catch(e){ /* no-op */ }
                }
            }
            """
        )
    )
    # Enable continuous scrolling inside the fixed frame (no pagination)
    gob.configure_pagination(enabled=False)
    gob.configure_default_column(editable=False, sortable=True, filter=True, resizable=True)

    grid_options = gob.build()

    # Wrap grid in a frame to constrain size and enable scroll similar to swipecards UX polish
    with st.container():
        st.markdown("<div class='edv-grid-frame'>", unsafe_allow_html=True)
        AgGrid(
            df,
            gridOptions=grid_options,
            height=420,  # CSS further constrains to 60vh via frame
            theme="streamlit",
            allow_unsafe_jscode=True,
            fit_columns_on_grid_load=True,
            key=f"ag_{table_key}",
        )
        st.markdown("</div>", unsafe_allow_html=True)


def _render_html_table(df: pd.DataFrame, errors: List[Dict[str, Any]], curr_idx: int) -> None:
    # Build error map for quick lookup
    error_map = _build_error_maps(errors)
    current = errors[curr_idx] if errors else None
    curr_row = int(current.get("row")) if current and current.get("row") is not None else None
    curr_col = str(current.get("col")) if current and current.get("col") is not None else None

    # Render a simple HTML table with classes applied
    headers = "".join(f"<th>{escape(str(h))}</th>" for h in df.columns)
    rows_html = []
    for r_idx, row in df.iterrows():
        cells = []
        for c in df.columns:
            classes = []
            if str(c) in error_map and r_idx in error_map[str(c)]:
                classes.append("error-cell")
            if curr_row == r_idx and curr_col == str(c):
                classes.append("current-error-cell")
            cls = f" class=\"{' '.join(classes)}\"" if classes else ""
            cells.append(f"<td{cls}>{escape(str(row[c]))}</td>")
        rows_html.append(f"<tr>{''.join(cells)}</tr>")

    table_html = f"""
    <div class="edv-table">
      <table>
        <thead><tr>{headers}</tr></thead>
        <tbody>{''.join(rows_html)}</tbody>
      </table>
    </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)


def render_error_detection_viewer(selected_dataset: str, propagated_errors: Dict[str, List[Dict[str, Any]]]) -> None:
    """Render tables list and, on click, load the selected table with error navigator.

    - Does not load any table until the user clicks its name.
    - Uses ag-Grid if available, or an HTML table fallback (non-Streamlit table).
    - Highlights all error cells and animates the current error cell when navigating.
    """
    _ensure_css_once()

    if not propagated_errors:
        st.info("No detected errors to display.")
        return

    # Show a list of tables as buttons; clicking loads just that table
    st.markdown("### Detected Errors")
    st.caption("Click a table to load it. Red highlight intensity indicates error focus.")

    # Sort tables for determinism
    table_names = sorted(propagated_errors.keys())

    cols = st.columns(3)
    for i, table in enumerate(table_names):
        errors = propagated_errors.get(table, [])
        btn_col = cols[i % 3]
        with btn_col:
            if st.button(f"📊 {table} ({len(errors)})", key=f"edv_btn_{table}", use_container_width=True):
                st.session_state["edv_active_table"] = table

    active_table: Optional[str] = st.session_state.get("edv_active_table")
    if not active_table:
        return

    st.markdown("---")
    st.subheader(f"📊 {active_table}")
    errors = propagated_errors.get(active_table, [])

    table_key = f"edv_{active_table}"
    curr_idx = _render_toolbar(table_key, errors)

    # Load the DataFrame only for the active table
    df = _load_table_df(selected_dataset, active_table)
    _render_aggrid(df, errors, curr_idx, table_key)
