import streamlit as st
import pandas as pd
import os
import time
import json
from backend import backend_dbf

# Set the page title and layout
st.set_page_config(page_title="Domain Based Folding", layout="wide")
st.title("Domain Based Folding")

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

# 🔄 Load dataset from pipeline config if not already in session_state
if "dataset_select" not in st.session_state and "pipeline_path" in st.session_state:
    config_path = os.path.join(st.session_state.pipeline_path, "configurations.json")
    if os.path.exists(config_path):
        with open(config_path) as f:
            config = json.load(f)
        st.session_state["dataset_select"] = config.get("selected_dataset", "Demo")

selected_dataset = st.session_state.get("dataset_select", "Demo")
# Use absolute path for datasets
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
datasets_path = os.path.join(root_dir, "datasets", selected_dataset)

# Load saved domain folds only if a pipeline is selected and table_locations is not already set.
if "pipeline_path" in st.session_state and "table_locations" not in st.session_state:
    pipeline_config_path = os.path.join(st.session_state.pipeline_path, "configurations.json")
    if os.path.exists(pipeline_config_path):
        with open(pipeline_config_path, "r") as f:
            pipeline_config = json.load(f)
        if "domain_folds" in pipeline_config:
            saved_folds = pipeline_config["domain_folds"]
            # Convert the saved fold structure {fold: [table1, table2, ...]} into our internal mapping {table: fold}
            st.session_state.table_locations = {
                table: fold for fold, tables in saved_folds.items() for table in tables
            }

# Initialize session state variables
if "merge_mode" not in st.session_state:
    st.session_state.merge_mode = False
if "selected_folds" not in st.session_state:
    st.session_state.selected_folds = []
if "global_split_mode" not in st.session_state:
    st.session_state.global_split_mode = False
if "selected_split_tables" not in st.session_state:
    st.session_state.selected_split_tables = {}
if "active_action" not in st.session_state:
    st.session_state.active_action = None

# Function to load the "clean.csv" file for a given table (i.e. subfolder)
def load_clean_table(table_name):
    file_path = os.path.join(datasets_path, table_name, "clean.csv")
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        df = pd.DataFrame({"Error": [f"Could not load {file_path}: {e}"]})
    return df

# Button to start domain folding
if st.button("▶️ Run Domain Based Folding"):
    with st.spinner("🔄 Processing... Please wait..."):
        # Call the backend function to get domain folds
        labeling_budget = st.session_state.get("labeling_budget", 10)  # Default to 10 if not set
        result = backend_dbf(selected_dataset, labeling_budget)
        domain_folds = result["domain_folds"]
        
        # Convert domain folds to table_locations format
        st.session_state.table_locations = {
            table: fold for fold, tables in domain_folds.items() for table in tables
        }
        time.sleep(2)  # Keep a small delay for UX
    st.session_state.run_folding = True

if st.session_state.get("run_folding"):
    st.markdown("---")

    # Group tables by their assigned fold
    domain_folds = {}
    for table, fold in st.session_state.table_locations.items():
        domain_folds.setdefault(fold, []).append(table)

    # OPTIONS / ACTION section
    st.markdown("### Options / Action")
    def set_action(action):
        st.session_state.active_action = action
        st.session_state.merge_mode = action == "merge"
        st.session_state.global_split_mode = action == "split"
        st.session_state.selected_folds = []
        st.session_state.selected_split_tables = {}

    merge_type = "primary" if st.session_state.active_action == "merge" else "secondary"
    split_type = "primary" if st.session_state.active_action == "split" else "secondary"

    st.markdown('<div class="action-container">', unsafe_allow_html=True)
    action_cols = st.columns(2)
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
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.active_action == "merge":
        st.info(
            "Merge Folds: Combine multiple domain folds into one. Select the folds you wish to merge, and all tables from those folds will be grouped under a single fold.",
            icon="ℹ️",
        )
    elif st.session_state.active_action == "split":
        st.info(
            "Split Folds: Divide a domain fold into separate folds. Choose the tables at which you want the split to occur; the folds will be split immediately below the selected tables, separating the tables into multiple groups.",
            icon="ℹ️",
        )

    st.markdown("---")
    st.markdown("### Fold / Table")
    
    # Iterate over each fold and display the tables
    for fold_name, tables in domain_folds.items():
        st.markdown('<div class="fold-row">', unsafe_allow_html=True)
        fold_cols = st.columns([0.03, 0.97], border=True)
        if st.session_state.merge_mode:
            merge_selected = fold_cols[0].checkbox(
                f"Select fold {fold_name}",
                key=f"merge_{fold_name}",
                label_visibility="collapsed",
            )
            if merge_selected and fold_name not in st.session_state.selected_folds:
                st.session_state.selected_folds.append(fold_name)
            elif not merge_selected and fold_name in st.session_state.selected_folds:
                st.session_state.selected_folds.remove(fold_name)
        else:
            fold_cols[0].empty()
        fold_cols[1].markdown(f"**{fold_name}**")
        st.markdown('</div>', unsafe_allow_html=True)

        # Display each table within the fold
        for table in tables:
            st.markdown('<div class="table-row">', unsafe_allow_html=True)
            table_cols = st.columns([0.03, 0.97], border=True)
            if st.session_state.global_split_mode:
                split_selected = table_cols[0].checkbox(
                    f"Select table {table}",
                    key=f"split_{fold_name}_{table}",
                    label_visibility="collapsed",
                )
                if fold_name not in st.session_state.selected_split_tables:
                    st.session_state.selected_split_tables[fold_name] = []
                selected_tables = st.session_state.selected_split_tables[fold_name]
                if split_selected and table not in selected_tables:
                    selected_tables.append(table)
                    st.session_state.selected_split_tables[fold_name] = selected_tables
                elif not split_selected and table in selected_tables:
                    selected_tables.remove(table)
                    st.session_state.selected_split_tables[fold_name] = selected_tables
            else:
                table_cols[0].empty()

            with table_cols[1].expander(f"📊 {table}"):
                df = load_clean_table(table)
                st.dataframe(df)
                new_location = st.radio(
                    f"Move {table} to:",
                    options=list(domain_folds.keys()),
                    index=list(domain_folds.keys()).index(st.session_state.table_locations[table]),
                    key=f"move_{table}"
                )
                if new_location != st.session_state.table_locations[table]:
                    st.session_state.table_locations[table] = new_location
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    
    # Global Confirm Merge: if merge mode is active and more than one fold is selected.
    if st.session_state.merge_mode and len(st.session_state.selected_folds) > 1:
        if st.button("Confirm Merge", key="confirm_merge"):
            target_fold = st.session_state.selected_folds[0]
            for fold in st.session_state.selected_folds[1:]:
                for table in domain_folds.get(fold, []):
                    st.session_state.table_locations[table] = target_fold
            st.session_state.selected_folds = []
            st.session_state.merge_mode = False
            st.session_state.active_action = None
        st.markdown("---")
    
    # Global Confirm Split: if split mode is active and at least one table is selected.
    if st.session_state.global_split_mode:
        any_split = any(st.session_state.selected_split_tables.get(fold, []) for fold in st.session_state.selected_split_tables)
        if any_split:
            if st.button("Confirm Split", key="confirm_split"):
                for fold_name, selected_tables in st.session_state.selected_split_tables.items():
                    if selected_tables:
                        tables_in_fold = domain_folds.get(fold_name, [])
                        indices = sorted([tables_in_fold.index(t) for t in selected_tables if t in tables_in_fold])
                        new_folds = []
                        prev_idx = 0
                        for idx in indices:
                            new_fold_name = f"{fold_name} - Split {len(domain_folds) + len(new_folds) + 1}"
                            new_folds.append(new_fold_name)
                            for t in tables_in_fold[prev_idx:idx + 1]:
                                st.session_state.table_locations[t] = new_fold_name
                            prev_idx = idx + 1
                        if prev_idx < len(tables_in_fold):
                            new_fold_name = f"{fold_name} - Split {len(domain_folds) + len(new_folds) + 1}"
                            for t in tables_in_fold[prev_idx:]:
                                st.session_state.table_locations[t] = new_fold_name
                st.session_state.global_split_mode = False
                st.session_state.selected_split_tables = {}
                st.session_state.active_action = None
            st.markdown("---")
    
    # Button to save the current domain fold structure to the pipeline's configurations.json file.
    if st.button("Save Domain Folds and Continue"):
        if "pipeline_path" in st.session_state:
            pipeline_config_path = os.path.join(st.session_state.pipeline_path, "configurations.json")
            if os.path.exists(pipeline_config_path):
                with open(pipeline_config_path, "r") as f:
                    pipeline_config = json.load(f)
            else:
                pipeline_config = {}
            domain_folds_to_save = {}
            for table, fold in st.session_state.table_locations.items():
                domain_folds_to_save.setdefault(fold, []).append(table)
            pipeline_config["domain_folds"] = domain_folds_to_save
            with open(pipeline_config_path, "w") as f:
                json.dump(pipeline_config, f, indent=4)
            st.success("Domain folds saved to pipeline configurations!")
        else:
            st.warning("No pipeline selected; domain folds not saved.")
    
    #if st.button("Next"):
        st.switch_page("pages/QualityBasedFolding.py")
