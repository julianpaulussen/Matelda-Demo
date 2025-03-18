import streamlit as st
import pandas as pd
import time
import os
import json

# Set page title and layout
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

# Get the dataset path from configurations; default to a hardcoded value if not set
datasets_path = st.session_state.get("dataset_path", os.path.join(os.path.dirname(__file__), "../datasets/Quintet"))

# --- Load previously saved quality folds if available ---
if "pipeline_path" in st.session_state and "table_locations" not in st.session_state:
    pipeline_config_path = os.path.join(st.session_state.pipeline_path, "configurations.json")
    if os.path.exists(pipeline_config_path):
        with open(pipeline_config_path, "r") as f:
            pipeline_config = json.load(f)
        if "quality_folds" in pipeline_config:
            saved_folds = pipeline_config["quality_folds"]
            # Convert the saved fold structure {fold: [table1, table2, ...]} into our internal mapping {table: fold}
            st.session_state.table_locations = {table: fold for fold, tables in saved_folds.items() for table in tables}

# Initialize session state variables for running the quality folding if not already set
if "run_quality_folding" not in st.session_state:
    st.session_state.run_quality_folding = False

# Initialize table_locations if not already set
if "table_locations" not in st.session_state:
    st.session_state.table_locations = {
        "Sales Data": "Quality Fold 1",
        "Customer Data": "Quality Fold 1",
        "Inventory Data": "Quality Fold 1",
        "Financial Report": "Quality Fold 2",
        "Employee Data": "Quality Fold 2",
        "Performance Metrics": "Quality Fold 3",
        "Risk Analysis": "Quality Fold 3"
    }

# Ensure merging and splitting related session state variables are available
if "merge_mode" not in st.session_state:
    st.session_state.merge_mode = False  
if "selected_folds" not in st.session_state:
    st.session_state.selected_folds = []  
if "global_split_mode" not in st.session_state:
    st.session_state.global_split_mode = False  
if "selected_split_tables" not in st.session_state:
    st.session_state.selected_split_tables = {}  

# Function to load the "clean.csv" file for a given table (i.e. subfolder)
def load_clean_table(table_name):
    file_path = os.path.join(datasets_path, table_name, "clean.csv")
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        df = pd.DataFrame({"Error": [f"Could not load {file_path}: {e}"]})
    return df

if st.button("Run Quality Based Folding"):
    with st.spinner("🔄 Processing... Please wait..."):
        time.sleep(3)  # Simulate delay
    st.session_state.run_quality_folding = True
    st.rerun()  # Refresh to show the tables

if st.session_state.run_quality_folding:
    st.markdown("---")
    
    # Global action header with Merge and Split buttons
    header_cols = st.columns([4, 1, 1])
    header_cols[0].markdown("**Fold / Table**")
    if header_cols[1].button("Merge Folds", key="global_merge_button_quality"):
        st.info("Select the Quality Folds to merge.", icon="ℹ️")
        st.session_state.merge_mode = True
        st.session_state.selected_folds = []
    if header_cols[2].button("Split Folds", key="global_split_button_quality"):
        st.info("Select the table at which you want to split the Quality Fold. The split will occur immediately below the chosen table.", icon="ℹ️")
        st.session_state.global_split_mode = True
        st.session_state.selected_split_tables = {}
    
    st.markdown("---")
    
    # Build quality folds from table_locations
    quality_folds = {}
    for table, fold in st.session_state.table_locations.items():
        quality_folds.setdefault(fold, []).append(table)
    
    # Iterate over each fold
    for fold_name, tables in quality_folds.items():
        fold_cols = st.columns([4, 1, 1])
        fold_cols[0].markdown(f"**{fold_name}**")
        if st.session_state.merge_mode:
            merge_selected = fold_cols[1].checkbox("Merge", key=f"merge_{fold_name}", label_visibility="hidden")
            if merge_selected and fold_name not in st.session_state.selected_folds:
                st.session_state.selected_folds.append(fold_name)
            elif not merge_selected and fold_name in st.session_state.selected_folds:
                st.session_state.selected_folds.remove(fold_name)
        else:
            fold_cols[1].empty()
        fold_cols[2].empty()
        
        # Iterate over each table in the fold
        for table in tables:
            table_cols = st.columns([4, 1, 1])
            with table_cols[0].expander(f"Quality Based Cell Fold: {table}"):
                st.dataframe(load_clean_table(table))
                # Radio button for moving the table to a different fold
                new_location = st.radio(
                    f"Move {table} to:",
                    options=list(quality_folds.keys()),
                    index=list(quality_folds.keys()).index(st.session_state.table_locations[table]),
                    key=f"move_{table}"
                )
                if new_location != st.session_state.table_locations[table]:
                    st.session_state.table_locations[table] = new_location
                    st.rerun()
            table_cols[1].empty()
            # Checkbox for splitting the table if global split mode is active
            if st.session_state.global_split_mode:
                split_selected = table_cols[2].checkbox("Split here", key=f"split_{fold_name}_{table}", label_visibility="hidden")
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
                table_cols[2].empty()
    
    st.markdown("---")
    
    # Global Confirm Merge if merge mode is active and more than one fold is selected
    if st.session_state.merge_mode and len(st.session_state.selected_folds) > 1:
        merge_confirm_cols = st.columns([4, 1, 1])
        if merge_confirm_cols[1].button("Confirm Merge", key="confirm_merge_quality"):
            target_fold = st.session_state.selected_folds[0]
            for fold in st.session_state.selected_folds[1:]:
                for table in quality_folds.get(fold, []):
                    st.session_state.table_locations[table] = target_fold
            st.session_state.selected_folds = []
            st.session_state.merge_mode = False
            st.rerun()
    
    # Global Confirm Split if split mode is active and at least one table is selected
    if st.session_state.global_split_mode:
        any_split = any(st.session_state.selected_split_tables.get(fold, []) for fold in st.session_state.selected_split_tables)
        if any_split:
            split_confirm_cols = st.columns([4, 1, 1])
            if split_confirm_cols[2].button("Confirm Split", key="confirm_split_quality"):
                for fold_name, selected_tables in st.session_state.selected_split_tables.items():
                    if selected_tables:
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
    
    st.markdown("---")
    
    # NEW: Button to save the current quality fold structure to the pipeline's configurations.json file.
    if st.button("Save Quality Folds"):
        if "pipeline_path" in st.session_state:
            pipeline_config_path = os.path.join(st.session_state.pipeline_path, "configurations.json")
            if os.path.exists(pipeline_config_path):
                with open(pipeline_config_path, "r") as f:
                    pipeline_config = json.load(f)
            else:
                pipeline_config = {}
            quality_folds_to_save = {}
            for table, fold in st.session_state.table_locations.items():
                quality_folds_to_save.setdefault(fold, []).append(table)
            pipeline_config["quality_folds"] = quality_folds_to_save
            with open(pipeline_config_path, "w") as f:
                json.dump(pipeline_config, f, indent=4)
            st.success("Quality folds saved to pipeline configurations!")
        else:
            st.warning("No pipeline selected; quality folds not saved.")
    
    if st.button("Next"):
        st.switch_page("pages/Labeling.py")
