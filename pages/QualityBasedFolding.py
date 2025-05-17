import streamlit as st
import pandas as pd
import os
import json
import time
import numpy as np
from backend import backend_qbf

# Page setup
st.set_page_config(page_title="Quality Based Folding", layout="wide")
st.title("Quality Based Folding")

# Hide default Streamlit menu
st.markdown(
    """
    <style>
        [data-testid=\"stSidebarNav\"] {display: none;}
    </style>
    """,
    unsafe_allow_html=True,
)

# JSON encoder for NumPy types and pandas types
def _json_default(obj):
    # NumPy arrays to lists
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    # NumPy scalar types (int, float, bool etc.) to native Python
    if isinstance(obj, np.generic):
        return obj.item()
    # pandas NA, boolean, integer, float
    try:
        import pandas as _pd
        if isinstance(obj, (_pd.NA.__class__,)):
            return None
        if isinstance(obj, (_pd.BooleanDtype().type, _pd.Int64Dtype().type, _pd.Float64Dtype().type)):
            return obj.item()
    except Exception:
        pass
    # Fallback for Python bool
    if isinstance(obj, bool):
        return obj
    raise TypeError(f"Type {obj.__class__.__name__} not serializable")

# Sidebar navigation
with st.sidebar:
    st.page_link("app.py", label="Matelda")
    st.page_link("pages/Configurations.py", label="Configurations")
    st.page_link("pages/DomainBasedFolding.py", label="Domain Based Folding")
    st.page_link("pages/QualityBasedFolding.py", label="Quality Based Folding")
    st.page_link("pages/Labeling.py", label="Labeling")
    st.page_link("pages/ErrorDetection.py", label="Error Detection")
    st.page_link("pages/Results.py", label="Results")

# Load selected dataset
if "dataset_select" not in st.session_state and "pipeline_path" in st.session_state:
    cfg_path = os.path.join(st.session_state.pipeline_path, "configurations.json")
    if os.path.exists(cfg_path):
        with open(cfg_path) as f:
            cfg = json.load(f)
        st.session_state.dataset_select = cfg.get("selected_dataset")

if "dataset_select" not in st.session_state:
    st.warning("⚠️ Please configure a dataset first.")
    st.stop()

# Paths
dataset = st.session_state.dataset_select
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
datasets_dir = os.path.join(root_dir, "datasets", dataset)

def load_clean_table(table_name):
    path = os.path.join(datasets_dir, table_name, "clean.csv")
    return pd.read_csv(path)

def highlight_cell(row_idx, col_name):
    def apply(df):
        return df.style.apply(
            lambda _: ['background-color: yellow' if i == row_idx else '' for i in range(len(df))],
            axis=0,
            subset=pd.IndexSlice[:, [col_name]]
        )
    return apply

# Load domain folds from config
if "domain_folds" not in st.session_state:
    if "pipeline_path" in st.session_state:
        cfg_path = os.path.join(st.session_state.pipeline_path, "configurations.json")
        if os.path.exists(cfg_path):
            with open(cfg_path) as f:
                cfg = json.load(f)
            st.session_state.domain_folds = cfg.get("domain_folds", {})
        else:
            st.warning("⚠️ No saved domain folds.")
            st.stop()
    else:
        st.warning("⚠️ No pipeline selected.")
        st.stop()

# Initialize controls
defaults = {
    "run_quality_folding": False,
    "merge_mode": False,
    "split_mode": False,
    "selected_folds_for_merge": [],  # List for merge mode
    "selected_cells_for_split": {}   # Dict for split mode
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# Run quality-based folding
if st.button("▶️ Run Quality Based Folding"):
    with st.spinner("🔄 Processing... Please wait..."):
        # Get labeling budget from configuration
        cfg_path = os.path.join(st.session_state.pipeline_path, "configurations.json")
        with open(cfg_path) as f:
            cfg = json.load(f)
        labeling_budget = cfg.get("labeling_budget", 10)
        
        # Call the backend function to get cell folds
        cell_folds = backend_qbf(
            selected_dataset=dataset,
            labeling_budget=labeling_budget,
            domain_folds=st.session_state.domain_folds
        )
        
        # Store the cell folds in session state
        st.session_state.cell_folds = cell_folds
        
        # Save to configuration file
        cfg["cell_folds"] = cell_folds
        with open(cfg_path, "w") as f:
            json.dump(cfg, f, indent=2, default=_json_default)
            
        time.sleep(2)  # Keep a small delay for UX
    st.session_state.run_quality_folding = True
    st.rerun()

if not st.session_state.run_quality_folding:
    st.stop()

st.markdown("---")

# Prepare fold mappings
all_folds = []
fold_to_domain = {}
for dom, folds in st.session_state.cell_folds.items():
    for fname in folds:
        all_folds.append(fname)
        fold_to_domain[fname] = dom

# Controls header
header_cols = st.columns([4, 1, 1])
header_cols[0].markdown("**Fold / Cell**")
if header_cols[1].button("Merge Folds", key="global_merge_button"):
    st.info("Merge Folds: Combine multiple cell folds into one. Select the folds you wish to merge, and all cells from those folds will be grouped under a single fold.", icon="ℹ️")
    st.session_state.merge_mode = True
    st.session_state.split_mode = False
    st.session_state.selected_folds_for_merge = []
    st.session_state.selected_cells_for_split = {}
if header_cols[2].button("Split Folds", key="global_split_button"):
    st.info("Split Folds: Divide a cell fold into separate folds. Choose the cells at which you want the split to occur; the folds will be split immediately below the selected cells, separating the cells into multiple groups.", icon="ℹ️")
    st.session_state.split_mode = True
    st.session_state.merge_mode = False
    st.session_state.selected_folds_for_merge = []
    st.session_state.selected_cells_for_split = {}

st.markdown("---")

# Display folds
for dom, folds in st.session_state.cell_folds.items():
    for fname, cell_list in folds.items():
        fold_cols = st.columns([4, 1, 1])
        fold_cols[0].markdown(f"📦 **{fname}**")
        if st.session_state.merge_mode:
            merge_selected = fold_cols[1].checkbox("Merge", key=f"merge_{fname}", label_visibility="hidden")
            if merge_selected and fname not in st.session_state.selected_folds_for_merge:
                st.session_state.selected_folds_for_merge.append(fname)
            elif not merge_selected and fname in st.session_state.selected_folds_for_merge:
                st.session_state.selected_folds_for_merge.remove(fname)
        else:
            fold_cols[1].empty()
        fold_cols[2].empty()

        for cell in cell_list:
            r, c, tbl, v = cell["row"], cell["col"], cell["table"], cell["val"]
            lbl = str(v)[:30] + "..." if isinstance(v, str) and len(v) > 30 else str(v)
            cell_cols = st.columns([4, 1, 1])
            with cell_cols[0]:
                with st.popover(lbl):
                    st.markdown(f"### 📄 Table: `{tbl}`")
                    st.markdown(f"**🔹 Column:** `{c}`  \n**🔹 Row Index:** `{r}`")
                    st.markdown("---")
                    st.markdown("### 🧠 Error Detection Strategies:")
                    if "strategies" in cell:
                        for strategy, is_active in cell["strategies"].items():
                            status = "✅" if is_active else "❌"
                            st.markdown(f"{status} {strategy}")
                    else:
                        st.info("🧬 No strategies available for this cell")
                    st.markdown("---")
                    st.markdown("### 🔍 Full Table Preview with Highlight")
                    df_preview = load_clean_table(tbl)
                    styled = highlight_cell(r, c)(df_preview)
                    st.dataframe(styled, use_container_width=True)
                    st.markdown("---")
                    st.markdown("### 🔁 Move to another fold")
                    new_loc = st.radio(
                        f"Move `{lbl}` to:",
                        all_folds,
                        index=all_folds.index(fname),
                        key=f"move_{tbl}_{r}_{c}"
                    )
                    if new_loc != fname:
                        old_dom = fold_to_domain[fname]
                        st.session_state.cell_folds[old_dom][fname].remove(cell)
                        new_dom = fold_to_domain[new_loc]
                        st.session_state.cell_folds[new_dom][new_loc].append(cell)
                        st.rerun()
            cell_cols[1].empty()
            if st.session_state.split_mode:
                split_selected = cell_cols[2].checkbox("Split here", key=f"split_{fname}_{tbl}_{r}_{c}", label_visibility="hidden")
                if fname not in st.session_state.selected_cells_for_split:
                    st.session_state.selected_cells_for_split[fname] = []
                selected_cells = st.session_state.selected_cells_for_split.get(fname, [])
                if split_selected and cell not in selected_cells:
                    selected_cells.append(cell)
                    st.session_state.selected_cells_for_split[fname] = selected_cells
                elif not split_selected and cell in selected_cells:
                    selected_cells.remove(cell)
                    st.session_state.selected_cells_for_split[fname] = selected_cells
            else:
                cell_cols[2].empty()

# Global Confirm Merge: if merge mode is active and more than one fold is selected
if st.session_state.merge_mode and len(st.session_state.selected_folds_for_merge) > 1:
    st.markdown("---")
    merge_confirm_cols = st.columns([4, 1, 1])
    if merge_confirm_cols[1].button("Confirm Merge", key="confirm_merge"):
        target_fold = st.session_state.selected_folds_for_merge[0]
        target_domain = fold_to_domain[target_fold]
        for fold in st.session_state.selected_folds_for_merge[1:]:
            source_domain = fold_to_domain[fold]
            # Extend target fold with cells from source fold
            st.session_state.cell_folds[target_domain][target_fold].extend(
                st.session_state.cell_folds[source_domain][fold]
            )
            # Remove the source fold
            del st.session_state.cell_folds[source_domain][fold]
        st.session_state.selected_folds_for_merge = []
        st.session_state.merge_mode = False
        st.rerun()

# Global Confirm Split: if split mode is active and at least one cell is selected
if st.session_state.split_mode:
    any_split = any(st.session_state.selected_cells_for_split.get(fold, []) for fold in st.session_state.selected_cells_for_split)
    if any_split:
        st.markdown("---")
        split_confirm_cols = st.columns([4, 1, 1])
        if split_confirm_cols[2].button("Confirm Split", key="confirm_split"):
            for fold_name, selected_cells in st.session_state.selected_cells_for_split.items():
                if selected_cells:
                    domain = fold_to_domain[fold_name]
                    cell_list = st.session_state.cell_folds[domain][fold_name]
                    # Get indices of selected cells
                    indices = sorted([cell_list.index(c) for c in selected_cells if c in cell_list])
                    
                    # Split the fold into segments
                    new_folds = []
                    prev_idx = 0
                    for idx in indices:
                        new_fold_name = f"{fold_name} - Split {len(new_folds) + 1}"
                        new_folds.append((new_fold_name, cell_list[prev_idx:idx + 1]))
                        prev_idx = idx + 1
                    
                    # Add remaining cells if any
                    if prev_idx < len(cell_list):
                        new_fold_name = f"{fold_name} - Split {len(new_folds) + 1}"
                        new_folds.append((new_fold_name, cell_list[prev_idx:]))
                    
                    # Remove the original fold and add new folds
                    del st.session_state.cell_folds[domain][fold_name]
                    for new_name, cells in new_folds:
                        st.session_state.cell_folds[domain][new_name] = cells
            
            st.session_state.split_mode = False
            st.session_state.selected_cells_for_split = {}
            st.rerun()

st.markdown("---")

# Save folds
if st.button("💾 Save Cell Folds", key="save_cell_folds"):
    if "pipeline_path" in st.session_state:
        cfg_path = os.path.join(st.session_state.pipeline_path, "configurations.json")
        with open(cfg_path, "r") as f:
            cfg = json.load(f)
        cfg["cell_folds"] = st.session_state.cell_folds
        with open(cfg_path, "w") as f:
            json.dump(cfg, f, indent=2, default=_json_default)
        st.success("✅ Saved.")
    else:
        st.warning("⚠️ No pipeline path set.")

# Next page button
if st.button("Next", key="next_page"):
    st.switch_page("pages/Labeling.py")
