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
      /* 1) Always hide the sidebar nav */
      [data-testid="stSidebarNav"] {
        display: none !important;
      }

      /* 2) Never wrap columns – always scroll if they overflow */
      [data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        overflow-x: auto !important;
      }
      [data-testid="stHorizontalBlock"] > div {
        /* strip only padding & margin on every column, but keep default min-width */
        padding: 0 !important;
      }

      /* 3) Let tables & checkboxes flow, but don’t force them smaller on desktop */
      [data-testid="stTable"],
      [data-testid="stCheckbox"] > div {
        flex: 0 0 auto !important;
      }

      /* 4) Mobile phones only: remove Streamlit’s min-width floors */
      @media (max-width: 768px) {
        .block-container {
          min-width: 0 !important;
        }
        [data-testid="stHorizontalBlock"] > div,
        [data-testid="stTable"],
        [data-testid="stCheckbox"] > div {
          min-width: 0 !important;
        }
      }
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
    st.page_link("pages/PropagatedErrors.py", label="Propagated Errors")
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
    "bulk_annotate_mode": False,  # New mode for bulk annotation
    "selected_folds_for_merge": [],  # List for merge mode
    "selected_cells_for_split": {},   # Dict for split mode
    "active_action": None,
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


def show_cell_dialog(cell, fold_name):
    r, c, tbl, v = cell["row"], cell["col"], cell["table"], cell["val"]
    lbl = str(v)[:30] + "..." if isinstance(v, str) and len(v) > 30 else str(v)

    @st.dialog(f"Details for {lbl}", width="large")
    def _dialog():
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
            index=all_folds.index(fold_name),
            key=f"move_{fold_name}_{tbl}_{r}_{c}_{id(cell)}"
        )
        if new_loc != fold_name:
            old_dom = fold_to_domain[fold_name]
            new_dom = fold_to_domain[new_loc]

            st.session_state.cell_folds[old_dom][fold_name].remove(cell)
            st.session_state.cell_folds[new_dom][new_loc].append(cell)

            if "pipeline_path" in st.session_state:
                cfg_path = os.path.join(st.session_state.pipeline_path, "configurations.json")
                with open(cfg_path, "r") as f:
                    cfg = json.load(f)
                cfg["cell_folds"] = st.session_state.cell_folds
                with open(cfg_path, "w") as f:
                    json.dump(cfg, f, indent=2, default=_json_default)

            st.rerun()
        if st.button("Close", key=f"close_{fold_name}_{tbl}_{r}_{c}_{id(cell)}"):
            st.rerun()

    _dialog()


# Controls header
st.markdown("### Options / Action")


def set_action(action):
    st.session_state.active_action = action
    st.session_state.merge_mode = action == "merge"
    st.session_state.split_mode = action == "split"
    st.session_state.bulk_annotate_mode = action == "bulk"
    st.session_state.selected_folds_for_merge = []
    st.session_state.selected_cells_for_split = {}


merge_type = "primary" if st.session_state.active_action == "merge" else "secondary"
split_type = "primary" if st.session_state.active_action == "split" else "secondary"
bulk_type = "primary" if st.session_state.active_action == "bulk" else "secondary"

st.markdown('<div class="action-container">', unsafe_allow_html=True)
action_cols = st.columns(3)
action_cols[0].button(
    "Merge Folds",
    key="global_merge_button",
    type=merge_type,
    on_click=set_action,
    args=("merge",),
    use_container_width=True,
)
action_cols[1].button(
    "Split Folds",
    key="global_split_button",
    type=split_type,
    on_click=set_action,
    args=("split",),
    use_container_width=True,
)
action_cols[2].button(
    "Bulk Annotate",
    key="global_bulk_button",
    type=bulk_type,
    on_click=set_action,
    args=("bulk",),
    use_container_width=True,
)
st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.active_action == "merge":
    st.info(
        "Merge Folds: Combine multiple cell folds into one. Select the folds you wish to merge, and all cells from those folds will be grouped under a single fold.",
        icon="ℹ️",
    )
elif st.session_state.active_action == "split":
    st.info(
        "Split Folds: Divide a cell fold into separate folds. Choose the cells at which you want the split to occur; the folds will be split immediately below the selected cells, separating the cells into multiple groups.",
        icon="ℹ️",
    )
elif st.session_state.active_action == "bulk":
    st.info(
        "Bulk Annotate: Label multiple cell folds at once as correct or incorrect. These labels will be used for error detection.",
        icon="ℹ️",
    )

st.markdown(
    """
    <style>
    div.action-container div[data-testid="stHorizontalBlock"] {
        gap:0 !important;
    }
    div.action-container div[data-testid="column"] {
        padding:0 !important;
    }
    div.action-container button {
        margin:0 !important;
    }
    div[data-testid="baseButton-primary"] > button {
        background-color: #ff4b4b;
        color: white;
    }
    div.fold-row div[data-testid="stHorizontalBlock"],
    div.cell-row div[data-testid="stHorizontalBlock"] {
        gap:0 !important;
    }
    div.fold-row div[data-testid="stHorizontalBlock"],
    div.cell-row div[data-testid="stHorizontalBlock"] {
        gap:0 !important;
    }
    div.fold-row div[data-testid="column"],
    div.cell-row div[data-testid="column"] {
        padding:0 !important;
    }
    div.fold-row [data-testid="stCheckbox"],
    div.cell-row [data-testid="stCheckbox"] {
        margin:0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")

st.markdown("### Fold / Cell")

# Display folds
for dom, folds in st.session_state.cell_folds.items():
    for fname, cell_list in folds.items():
        # Get the label for this fold if it exists
        fold_label = None
        if "pipeline_path" in st.session_state:
            cfg_path = os.path.join(st.session_state.pipeline_path, "configurations.json")
            if os.path.exists(cfg_path):
                with open(cfg_path) as f:
                    cfg = json.load(f)
                fold_label = cfg.get("cell_fold_labels", {}).get(fname, "neutral")
        
        # Set color based on label
        label_color = {
            "correct": "green",
            "false": "red",
            "neutral": None  # No color for neutral, will use default
        }.get(fold_label)
        
        st.markdown('<div class="fold-row">', unsafe_allow_html=True)
        fold_cols = st.columns([0.04, 0.76, 0.20])

        if st.session_state.merge_mode:
            merge_selected = fold_cols[0].checkbox(
                f"Select fold {fname}",
                key=f"merge_{fname}",
                label_visibility="collapsed",
            )
            if merge_selected and fname not in st.session_state.selected_folds_for_merge:
                st.session_state.selected_folds_for_merge.append(fname)
            elif not merge_selected and fname in st.session_state.selected_folds_for_merge:
                st.session_state.selected_folds_for_merge.remove(fname)
        else:
            fold_cols[0].empty()

        if label_color:
            fold_cols[1].markdown(
                f'📦 **<span style="color: {label_color}">{fname}</span>**',
                unsafe_allow_html=True,
            )
        else:
            fold_cols[1].markdown(f"📦 **{fname}**")

        if st.session_state.bulk_annotate_mode:
            button_cols = fold_cols[2].columns(2)
            if button_cols[0].button("✓", key=f"correct_{fname}"):
                if "pipeline_path" in st.session_state:
                    cfg_path = os.path.join(
                        st.session_state.pipeline_path, "configurations.json"
                    )
                    if os.path.exists(cfg_path):
                        with open(cfg_path) as f:
                            cfg = json.load(f)
                        if "cell_fold_labels" not in cfg:
                            cfg["cell_fold_labels"] = {}
                        cfg["cell_fold_labels"][fname] = "correct"
                        with open(cfg_path, "w") as f:
                            json.dump(cfg, f, indent=2, default=_json_default)
                        st.rerun()
            if button_cols[1].button("✗", key=f"false_{fname}"):
                if "pipeline_path" in st.session_state:
                    cfg_path = os.path.join(
                        st.session_state.pipeline_path, "configurations.json"
                    )
                    if os.path.exists(cfg_path):
                        with open(cfg_path) as f:
                            cfg = json.load(f)
                        if "cell_fold_labels" not in cfg:
                            cfg["cell_fold_labels"] = {}
                        cfg["cell_fold_labels"][fname] = "false"
                        with open(cfg_path, "w") as f:
                            json.dump(cfg, f, indent=2, default=_json_default)
                        st.rerun()
        else:
            fold_cols[2].empty()
        st.markdown('</div>', unsafe_allow_html=True)

        for cell_idx, cell in enumerate(cell_list):
            r, c, tbl, v = cell["row"], cell["col"], cell["table"], cell["val"]
            lbl = str(v)[:30] + "..." if isinstance(v, str) and len(v) > 30 else str(v)
            st.markdown('<div class="cell-row">', unsafe_allow_html=True)
            cell_cols = st.columns([0.03, 0.97])
            if st.session_state.split_mode:
                split_selected = cell_cols[0].checkbox(
                    f"Select cell {tbl}-{r}-{c}",
                    key=f"split_{fname}_{tbl}_{r}_{c}_{cell_idx}",
                    label_visibility="collapsed",
                )
                if fname not in st.session_state.selected_cells_for_split:
                    st.session_state.selected_cells_for_split[fname] = []
                selected_cells = st.session_state.selected_cells_for_split.get(
                    fname, []
                )
                if split_selected and cell not in selected_cells:
                    selected_cells.append(cell)
                    st.session_state.selected_cells_for_split[fname] = selected_cells
                elif not split_selected and cell in selected_cells:
                    selected_cells.remove(cell)
                    st.session_state.selected_cells_for_split[fname] = selected_cells
            else:
                cell_cols[0].empty()

            if cell_cols[1].button(
                lbl, key=f"cell_{fname}_{tbl}_{r}_{c}_{cell_idx}"
            ):
                show_cell_dialog(cell, fname)
            st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# Global Confirm Merge: if merge mode is active and more than one fold is selected
if st.session_state.merge_mode and len(st.session_state.selected_folds_for_merge) > 1:
    if st.button("Confirm Merge", key="confirm_merge"):
        target_fold = st.session_state.selected_folds_for_merge[0]
        target_domain = fold_to_domain[target_fold]
        
        # Get the labels of all folds being merged
        cfg_path = os.path.join(st.session_state.pipeline_path, "configurations.json")
        with open(cfg_path, "r") as f:
            cfg = json.load(f)
        
        fold_labels = cfg.get("cell_fold_labels", {})
        labels_to_merge = [fold_labels.get(fold, "neutral") for fold in st.session_state.selected_folds_for_merge]
        
        # Determine the final label based on the rules
        has_correct = "correct" in labels_to_merge
        has_false = "false" in labels_to_merge
        all_correct_or_neutral = all(label in ["correct", "neutral"] for label in labels_to_merge)
        
        # Apply the rules
        if has_correct and has_false:
            final_label = "neutral"  # Rule: if conflict between correct and false -> neutral
        elif all_correct_or_neutral and has_correct:
            final_label = "correct"  # Rule: if all are correct or neutral, and at least one correct -> correct
        elif has_false:
            final_label = "false"    # Rule: if any false and no correct -> false
        else:
            final_label = "neutral"  # Default case
        
        # Update the label for the target fold
        if "cell_fold_labels" not in cfg:
            cfg["cell_fold_labels"] = {}
        cfg["cell_fold_labels"][target_fold] = final_label
        
        # Remove labels for the source folds that will be deleted
        for fold in st.session_state.selected_folds_for_merge[1:]:
            if fold in cfg["cell_fold_labels"]:
                del cfg["cell_fold_labels"][fold]
        
        # Perform the merge
        for fold in st.session_state.selected_folds_for_merge[1:]:
            source_domain = fold_to_domain[fold]
            # Extend target fold with cells from source fold
            st.session_state.cell_folds[target_domain][target_fold].extend(
                st.session_state.cell_folds[source_domain][fold]
            )
            # Remove the source fold
            del st.session_state.cell_folds[source_domain][fold]
        
        # Save the updated configuration
        with open(cfg_path, "w") as f:
            json.dump(cfg, f, indent=2, default=_json_default)
        
        st.session_state.selected_folds_for_merge = []
        st.session_state.merge_mode = False
        st.rerun()
    st.markdown("---")

# Global Confirm Split: if split mode is active and at least one cell is selected
if st.session_state.split_mode:
    any_split = any(
        st.session_state.selected_cells_for_split.get(fold, [])
        for fold in st.session_state.selected_cells_for_split
    )
    if any_split:
        if st.button("Confirm Split", key="confirm_split"):
            for fold_name, selected_cells in st.session_state.selected_cells_for_split.items():
                if selected_cells:
                    domain = fold_to_domain[fold_name]
                    cell_list = st.session_state.cell_folds[domain][fold_name]
                    # Get indices of selected cells
                    indices = sorted(
                        [cell_list.index(c) for c in selected_cells if c in cell_list]
                    )

                    # Split the fold into segments
                    new_folds = []
                    prev_idx = 0
                    for idx in indices:
                        new_fold_name = f"{fold_name} - Split {len(new_folds) + 1}"
                        new_folds.append((new_fold_name, cell_list[prev_idx : idx + 1]))
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
if st.button("💾 Save Cell Folds and Continue", key="save_cell_folds"):
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
# if st.button("Next", key="next_page"):
    st.switch_page("pages/Labeling.py")
