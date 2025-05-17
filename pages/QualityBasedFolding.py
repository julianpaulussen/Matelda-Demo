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
    "selected_cell_folds": []
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
header = st.columns([5, 1, 1])
header[0].markdown("**Fold / Cell**")
if header[1].button("Merge"):
    st.session_state.merge_mode = True
    st.session_state.split_mode = False
    st.session_state.selected_cell_folds = []
if header[2].button("Split"):
    st.session_state.split_mode = True
    st.session_state.merge_mode = False
    st.session_state.selected_cell_folds = []

# Display folds
for dom, folds in st.session_state.cell_folds.items():
    for fname, cell_list in folds.items():
        st.markdown("---")
        cols = st.columns([5, 1, 1])
        cols[0].markdown(f"📦 **{fname}**")
        if st.session_state.merge_mode:
            chk = cols[1].checkbox("✔", key=f"merge_{fname}", label_visibility="collapsed")
            if chk and fname not in st.session_state.selected_cell_folds:
                st.session_state.selected_cell_folds.append(fname)
            if not chk and fname in st.session_state.selected_cell_folds:
                st.session_state.selected_cell_folds.remove(fname)
        else:
            cols[1].empty()
        cols[2].empty()

        for cell in cell_list:
            r, c, tbl, v = cell["row"], cell["col"], cell["table"], cell["val"]
            lbl = str(v)[:30] + "..." if isinstance(v, str) and len(v) > 30 else str(v)
            rowcols = st.columns([5, 1, 1])
            with rowcols[0]:
                with st.popover(lbl):
                    st.markdown(f"### 📄 Table: `{tbl}`")
                    st.markdown(f"**🔹 Column:** `{c}`  \n**🔹 Row Index:** `{r}`")
                    st.markdown("---")
                    st.markdown("### 🧠 Error Detection Strategies:")
                    st.info("🧬 Placeholder for strategy pills or toggles...")
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

        # Merge confirm
        if st.session_state.merge_mode and len(st.session_state.selected_cell_folds) > 1:
            st.markdown("---")
            if st.button("✅ Confirm Merge"):
                tgt = st.session_state.selected_cell_folds[0]
                for oth in st.session_state.selected_cell_folds[1:]:
                    dom_tgt = fold_to_domain[tgt]
                    dom_oth = fold_to_domain[oth]
                    st.session_state.cell_folds[dom_tgt][tgt].extend(
                        st.session_state.cell_folds[dom_oth][oth]
                    )
                    del st.session_state.cell_folds[dom_oth][oth]
                st.session_state.merge_mode = False
                st.session_state.selected_cell_folds = []
                st.rerun()

        # Split confirm
        if st.session_state.split_mode and any(isinstance(x, dict) for x in st.session_state.selected_cell_folds):
            st.markdown("---")
            if st.button("✅ Confirm Split"):
                for dom, frags in st.session_state.cell_folds.items():
                    new_frags = {}
                    for name, clist in list(frags.items()):
                        segments, cur = [], []
                        for item in clist:
                            cur.append(item)
                            if item in st.session_state.selected_cell_folds:
                                segments.append(cur)
                                cur = []
                        if cur:
                            segments.append(cur)
                        del frags[name]
                        for i, seg in enumerate(segments):
                            new_frags[f"{name} - Split {i+1}"] = seg
                        st.session_state.cell_folds[dom].update(new_frags)
                st.session_state.split_mode = False
                st.session_state.selected_cell_folds = []
                st.rerun()

st.markdown("---")
# Save folds
if st.button("💾 Save Cell Folds"):
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
if st.button("Next"):
    st.switch_page("pages/Labeling.py")
