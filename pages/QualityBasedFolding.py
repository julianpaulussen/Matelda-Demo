import streamlit as st
import pandas as pd
import os
import json
import random
import time

st.set_page_config(page_title="Quality Based Folding", layout="wide")
st.title("Quality Based Folding")

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
    st.page_link("pages/ErrorDetection.py", label="Error Detection")
    st.page_link("pages/Results.py", label="Results")

# Load dataset
if "dataset_select" not in st.session_state and "pipeline_path" in st.session_state:
    config_path = os.path.join(st.session_state.pipeline_path, "configurations.json")
    if os.path.exists(config_path):
        with open(config_path) as f:
            config = json.load(f)
        st.session_state["dataset_select"] = config.get("selected_dataset")

if "dataset_select" not in st.session_state:
    st.warning("⚠️ Please configure a dataset first.")
    st.stop()

dataset = st.session_state["dataset_select"]
datasets_path = os.path.join(os.path.dirname(__file__), "../datasets", dataset)

def load_clean_table(table_name):
    path = os.path.join(datasets_path, table_name, "clean.csv")
    return pd.read_csv(path)

def highlight_cell(row_idx, col_name):
    def apply(df):
        return df.style.map(
            lambda _: "background-color: yellow",
            subset=pd.IndexSlice[[row_idx], [col_name]]
        )
    return apply

# Load domain folds
if "domain_folds" not in st.session_state:
    if "pipeline_path" in st.session_state:
        config_path = os.path.join(st.session_state.pipeline_path, "configurations.json")
        if os.path.exists(config_path):
            with open(config_path) as f:
                config = json.load(f)
            st.session_state.domain_folds = config.get("domain_folds", {})
        else:
            st.warning("⚠️ No saved domain folds.")
            st.stop()
    else:
        st.warning("⚠️ No pipeline selected.")
        st.stop()

# Session state init
for k, v in {
    "run_quality_folding": False,
    "merge_mode": False,
    "split_mode": False,
    "selected_cell_folds": [],
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Run folding
if st.button("▶️ Run Quality Based Folding"):
    with st.spinner("🔄 Processing... Please wait..."):
        time.sleep(2)
        st.session_state.cell_folds = {}
        for domain_fold, tables in st.session_state.domain_folds.items():
            num_cell_folds = random.randint(1, 2)
            cell_fold_names = [f"{domain_fold} / Cell Fold {i+1}" for i in range(num_cell_folds)]
            all_cells = []
            for table in tables:
                df = load_clean_table(table)
                for _ in range(random.randint(3, 5)):
                    row_idx = random.randint(0, df.shape[0] - 1)
                    col = random.choice(df.columns)
                    val = df.at[row_idx, col]
                    all_cells.append({"table": table, "row": row_idx, "col": col, "val": val})
            random.shuffle(all_cells)
            splits = [all_cells[i::num_cell_folds] for i in range(num_cell_folds)]
            st.session_state.cell_folds[domain_fold] = {
                name: split for name, split in zip(cell_fold_names, splits)
            }
    st.session_state.run_quality_folding = True
    st.rerun()

if not st.session_state.run_quality_folding:
    st.info("Click ▶️ to begin.")
    st.stop()

st.markdown("---")

# Collect fold info
all_cell_fold_names = []
cell_fold_to_domain = {}
for domain_fold, cell_folds in st.session_state.cell_folds.items():
    for cf_name in cell_folds:
        all_cell_fold_names.append(cf_name)
        cell_fold_to_domain[cf_name] = domain_fold

# Controls
#controls = st.columns([6, 1, 1])
#if controls[1].button("Merge Folds"):
#    st.session_state.merge_mode = True
#    st.session_state.split_mode = False
#    st.session_state.selected_cell_folds = []

#if controls[2].button("Split Folds"):
#    st.session_state.split_mode = True
#    st.session_state.merge_mode = False
#    st.session_state.selected_cell_folds = []

# Header row
#header = st.columns([5, 1, 1])
#header[0].markdown("**Fold / Cell**")
#header[1].markdown("**Merge**")
#header[2].markdown("**Split**")
# Header row with buttons
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


# Display folds and cells
for domain_fold, cell_folds in st.session_state.cell_folds.items():
    for fold_name, cell_list in cell_folds.items():
        st.markdown("---")
        row = st.columns([5, 1, 1])
        row[0].markdown(f"📦 **{fold_name}**")
        if st.session_state.merge_mode:
            merge_selected = row[1].checkbox("✔", key=f"merge_{fold_name}", label_visibility="collapsed")
            if merge_selected and fold_name not in st.session_state.selected_cell_folds:
                st.session_state.selected_cell_folds.append(fold_name)
            elif not merge_selected and fold_name in st.session_state.selected_cell_folds:
                st.session_state.selected_cell_folds.remove(fold_name)
        else:
            row[1].empty()
        row[2].empty()
        

        for i, cell in enumerate(cell_list):
            row_idx, col_name, table, val = cell["row"], cell["col"], cell["table"], cell["val"]
            label = str(val)[:30] + "..." if len(str(val)) > 30 else str(val)

            cell_row = st.columns([5, 1, 1])
            with cell_row[0]:
                with st.popover(label):
                    st.markdown(f"### 📄 Table: `{table}`")
                    st.markdown(f"**🔹 Column:** `{col_name}`  \n**🔹 Row Index:** `{row_idx}`")

                    st.markdown("---")
                    st.markdown("### 🧠 Error Detection Strategies:")
                    st.info("🧬 Placeholder for strategy pills or toggles...")

                    st.markdown("---")
                    st.markdown("### 🔍 Full Table Preview with Highlight")
                    df = load_clean_table(table)
                    styled = highlight_cell(row_idx, col_name)(df)
                    st.dataframe(styled, use_container_width=True)

                    st.markdown("---")
                    st.markdown("### 🔁 Move table to another fold")
                    new_loc = st.radio(
                        f"Move `{val}` to:",
                        all_cell_fold_names,
                        index=all_cell_fold_names.index(fold_name),
                        key=f"move_{table}_{row_idx}_{col_name}"
                    )
                    if new_loc != fold_name:
                        st.session_state.cell_folds[domain_fold][fold_name].remove(cell)
                        new_domain = cell_fold_to_domain[new_loc]
                        st.session_state.cell_folds[new_domain][new_loc].append(cell)
                        st.rerun()

                    if new_loc != fold_name:
                        st.session_state.cell_folds[domain_fold][fold_name].remove(cell)
                        new_domain = cell_fold_to_domain[new_loc]
                        st.session_state.cell_folds[new_domain][new_loc].append(cell)
                        st.rerun()

            cell_row[1].empty()
            if st.session_state.split_mode:
                checked = cell in st.session_state.selected_cell_folds
                if cell_row[2].checkbox("✂", key=f"split_{fold_name}_{i}", value=checked, label_visibility="collapsed"):
                    if cell not in st.session_state.selected_cell_folds:
                        st.session_state.selected_cell_folds.append(cell)
                else:
                    if cell in st.session_state.selected_cell_folds:
                        st.session_state.selected_cell_folds.remove(cell)
            else:
                cell_row[2].empty()
            

# Confirm merge
if st.session_state.merge_mode and len(st.session_state.selected_cell_folds) > 1:
    st.markdown("---")
    if st.button("✅ Confirm Merge"):
        target = st.session_state.selected_cell_folds[0]
        target_domain = cell_fold_to_domain[target]
        for other in st.session_state.selected_cell_folds[1:]:
            other_domain = cell_fold_to_domain[other]
            st.session_state.cell_folds[target_domain][target].extend(
                st.session_state.cell_folds[other_domain][other]
            )
            del st.session_state.cell_folds[other_domain][other]
        st.session_state.merge_mode = False
        st.session_state.selected_cell_folds = []
        st.rerun()

# Confirm split
if st.session_state.split_mode and any(isinstance(c, dict) for c in st.session_state.selected_cell_folds):
    st.markdown("---")
    if st.button("✅ Confirm Split"):
        for domain_fold, folds in st.session_state.cell_folds.items():
            new_folds = {}
            for fold_name, cell_list in list(folds.items()):
                splits, current = [], []
                for cell in cell_list:
                    current.append(cell)
                    if cell in st.session_state.selected_cell_folds:
                        splits.append(current)
                        current = []
                if current:
                    splits.append(current)
                del folds[fold_name]
                for i, s in enumerate(splits):
                    new_folds[f"{fold_name} - Split {i+1}"] = s
            st.session_state.cell_folds[domain_fold].update(new_folds)
        st.session_state.split_mode = False
        st.session_state.selected_cell_folds = []
        st.rerun()

st.markdown("---")

# Save button
if st.button("💾 Save Cell Folds"):
    if "pipeline_path" in st.session_state:
        config_path = os.path.join(st.session_state.pipeline_path, "configurations.json")
        with open(config_path, "r") as f:
            config = json.load(f)
        config["cell_folds"] = st.session_state.cell_folds
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        st.success("✅ Saved.")
    else:
        st.warning("⚠️ No pipeline path set.")

if st.button("Next"):
    st.switch_page("pages/Labeling.py")
