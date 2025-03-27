import streamlit as st
import pandas as pd
import time
import os
import json
import random

st.set_page_config(page_title="Quality Based Folding", layout="wide")
st.title("Quality Based Folding")

# Hide sidebar nav
st.markdown("<style>[data-testid='stSidebarNav'] {display: none;}</style>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.page_link("app.py", label="Matelda")
    st.page_link("pages/Configurations.py", label="Configurations")
    st.page_link("pages/DomainBasedFolding.py", label="Domain Based Folding")
    st.page_link("pages/QualityBasedFolding.py", label="Quality Based Folding")
    st.page_link("pages/Labeling.py", label="Labeling")
    st.page_link("pages/ErrorDetection.py", label="Error Detection")
    st.page_link("pages/Results.py", label="Results")

# Load dataset selection from config if needed
if "dataset_select" not in st.session_state and "pipeline_path" in st.session_state:
    config_path = os.path.join(st.session_state.pipeline_path, "configurations.json")
    if os.path.exists(config_path):
        with open(config_path) as f:
            config = json.load(f)
        st.session_state["dataset_select"] = config.get("selected_dataset", "Quintet")

selected_dataset = st.session_state.get("dataset_select", "Quintet")
datasets_path = os.path.join(os.path.dirname(__file__), "../datasets", selected_dataset)

# Load table fold mapping from config
if "pipeline_path" in st.session_state and "table_locations" not in st.session_state:
    config_path = os.path.join(st.session_state.pipeline_path, "configurations.json")
    if os.path.exists(config_path):
        with open(config_path) as f:
            config = json.load(f)
        if "quality_folds" in config:
            st.session_state.table_locations = {
                table: fold for fold, tables in config["quality_folds"].items() for table in tables
            }

if "table_locations" not in st.session_state:
    st.session_state.table_locations = {}

# Session state flags
if "run_quality_folding" not in st.session_state:
    st.session_state.run_quality_folding = False
if "merge_mode" not in st.session_state:
    st.session_state.merge_mode = False
if "selected_folds" not in st.session_state:
    st.session_state.selected_folds = []
if "global_split_mode" not in st.session_state:
    st.session_state.global_split_mode = False
if "selected_split_tables" not in st.session_state:
    st.session_state.selected_split_tables = {}
if "sampled_cells" not in st.session_state:
    st.session_state.sampled_cells = {}

# Load full table
def load_clean_table(table_name):
    path = os.path.join(datasets_path, table_name, "clean.csv")
    try:
        df = pd.read_csv(path)
    except Exception as e:
        df = pd.DataFrame({"Error": [f"Could not load {path}: {e}"]})
    return df

# Sample a random cell
def sample_cell(df):
    if df.empty:
        return None, None, None
    row_idx = random.randint(0, len(df) - 1)
    col = random.choice(df.columns.tolist())
    val = df.iloc[row_idx][col]
    return row_idx, col, val

# Highlight only 1 cell
def highlight_cell(row_idx, col_name):
    def apply_highlight(df):
        styled_df = df.style
        styled_df = styled_df.map(
            lambda val: "background-color: #FFD700; font-weight: bold",
            subset=pd.IndexSlice[[row_idx], [col_name]]
        )
        return styled_df
    return apply_highlight


# Run folding and sample all tables
if st.button("Run Quality Based Folding"):
    with st.spinner("🔄 Sampling cells..."):
        st.session_state.sampled_cells = {}
        all_tables = list(st.session_state.table_locations.keys())
        for table in all_tables:
            df = load_clean_table(table)
            row_idx, col, val = sample_cell(df)
            if row_idx is not None and col is not None:
                st.session_state.sampled_cells[table] = {"row": row_idx, "col": col, "val": val}
        st.session_state.run_quality_folding = True
    st.rerun()

# Auto-fill missing samples if needed
if st.session_state.run_quality_folding:
    for table in st.session_state.table_locations:
        if table not in st.session_state.sampled_cells:
            df = load_clean_table(table)
            row_idx, col, val = sample_cell(df)
            if row_idx is not None and col is not None:
                st.session_state.sampled_cells[table] = {"row": row_idx, "col": col, "val": val}

# UI
if st.session_state.run_quality_folding:
    st.markdown("---")

    quality_folds = {}
    for table, fold in st.session_state.table_locations.items():
        quality_folds.setdefault(fold, []).append(table)

    # Header buttons
    header_cols = st.columns([4, 1, 1])
    header_cols[0].markdown("**Fold / Table**")
    if header_cols[1].button("Merge Folds", key="global_merge_button_quality"):
        st.info("Select the Quality Folds to merge.", icon="ℹ️")
        st.session_state.merge_mode = True
        st.session_state.selected_folds = []
    if header_cols[2].button("Split Folds", key="global_split_button_quality"):
        st.info("Select the table to split the fold below.", icon="ℹ️")
        st.session_state.global_split_mode = True
        st.session_state.selected_split_tables = {}

    st.markdown("---")

    for fold_name, tables in quality_folds.items():
        fold_cols = st.columns([4, 1, 1])
        fold_cols[0].markdown(f"### 🧩 {fold_name}")

        if st.session_state.merge_mode:
            merge_selected = fold_cols[1].checkbox("Merge", key=f"merge_{fold_name}", label_visibility="hidden")
            if merge_selected and fold_name not in st.session_state.selected_folds:
                st.session_state.selected_folds.append(fold_name)
            elif not merge_selected and fold_name in st.session_state.selected_folds:
                st.session_state.selected_folds.remove(fold_name)
        else:
            fold_cols[1].empty()
        fold_cols[2].empty()

        for table in tables:
            df = load_clean_table(table)
            cell_info = st.session_state.sampled_cells.get(table, None)

            if cell_info:
                row_idx = cell_info["row"]
                col_name = cell_info["col"]
                cell_value = cell_info["val"]
                label = str(cell_value)[:30] + "..." if len(str(cell_value)) > 30 else str(cell_value)

                table_cols = st.columns([5, 1, 1])
                with table_cols[0].popover(label):
                    st.markdown(f"### 📄 Table: `{table}`")
                    st.markdown(f"- **Column**: `{col_name}`")
                    st.markdown(f"- **Row Index**: `{row_idx}`")
                    st.markdown("#### 🧪 Error Detection Strategies:")
                    st.info("🚧 Placeholder for strategy pills or toggles...", icon="🧠")
                    st.markdown("#### 🔍 Full Table Preview with Highlight")
                    styled_df = highlight_cell(row_idx, col_name)(df)
                    st.dataframe(styled_df, use_container_width=True)

                    st.markdown("#### 🔁 Move table to another fold")
                    new_location = st.radio(
                        f"Move `{table}` to:",
                        options=list(quality_folds.keys()),
                        index=list(quality_folds.keys()).index(st.session_state.table_locations[table]),
                        key=f"move_{table}"
                    )
                    if new_location != st.session_state.table_locations[table]:
                        st.session_state.table_locations[table] = new_location
                        st.rerun()

                if st.session_state.global_split_mode:
                    split_selected = table_cols[2].checkbox("Split here", key=f"split_{fold_name}_{table}", label_visibility="hidden")
                    if fold_name not in st.session_state.selected_split_tables:
                        st.session_state.selected_split_tables[fold_name] = []
                    selected_tables = st.session_state.selected_split_tables[fold_name]
                    if split_selected and table not in selected_tables:
                        selected_tables.append(table)
                    elif not split_selected and table in selected_tables:
                        selected_tables.remove(table)
                else:
                    table_cols[2].empty()
            else:
                st.warning(f"⚠️ No sampled cell found for `{table}`.")

    st.divider()

    # Confirm Merge
    if st.session_state.merge_mode and len(st.session_state.selected_folds) > 1:
        merge_cols = st.columns([4, 1, 1])
        if merge_cols[1].button("Confirm Merge", key="confirm_merge_quality"):
            target_fold = st.session_state.selected_folds[0]
            for fold in st.session_state.selected_folds[1:]:
                for table in quality_folds.get(fold, []):
                    st.session_state.table_locations[table] = target_fold
            st.session_state.merge_mode = False
            st.session_state.selected_folds = []
            st.rerun()

    # Confirm Split
    if st.session_state.global_split_mode:
        any_split = any(st.session_state.selected_split_tables.get(f, []) for f in st.session_state.selected_split_tables)
        if any_split:
            split_cols = st.columns([4, 1, 1])
            if split_cols[2].button("Confirm Split", key="confirm_split_quality"):
                for fold_name, selected_tables in st.session_state.selected_split_tables.items():
                    tables_in_fold = quality_folds.get(fold_name, [])
                    indices = sorted([tables_in_fold.index(t) for t in selected_tables if t in tables_in_fold])
                    new_folds = []
                    prev_idx = 0
                    for idx in indices:
                        new_fold_name = f"{fold_name} - Split {len(quality_folds) + len(new_folds) + 1}"
                        new_folds.append(new_fold_name)
                        for t in tables_in_fold[prev_idx:idx + 1]:
                            st.session_state.table_locations[t] = new_fold_name
                        prev_idx = idx + 1
                    if prev_idx < len(tables_in_fold):
                        new_fold_name = f"{fold_name} - Split {len(quality_folds) + len(new_folds) + 1}"
                        for t in tables_in_fold[prev_idx:]:
                            st.session_state.table_locations[t] = new_fold_name
                st.session_state.global_split_mode = False
                st.session_state.selected_split_tables = {}
                st.rerun()

    # Save
    if st.button("Save Quality Folds"):
        if "pipeline_path" in st.session_state:
            config_path = os.path.join(st.session_state.pipeline_path, "configurations.json")
            config = {}
            if os.path.exists(config_path):
                with open(config_path) as f:
                    config = json.load(f)
            config["quality_folds"] = {}
            for table, fold in st.session_state.table_locations.items():
                config["quality_folds"].setdefault(fold, []).append(table)
            with open(config_path, "w") as f:
                json.dump(config, f, indent=4)
            st.success("✅ Quality folds saved to pipeline configurations.")
        else:
            st.warning("⚠️ No pipeline selected.")

    if st.button("Next"):
        st.switch_page("pages/Labeling.py")
