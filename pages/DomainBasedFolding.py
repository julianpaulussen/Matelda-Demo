import streamlit as st
import pandas as pd
import os
import random
import time

# Set the page title and layout
st.set_page_config(page_title="Domain Based Folding", layout="wide")
st.title("Domain Based Folding")

# Hide default Streamlit menu
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] {display: none;}
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
    st.page_link("pages/ErrorDetection.py", label="Error Detection")
    st.page_link("pages/Results.py", label="Results")

# Initialize session state variables if not already set
if "run_folding" not in st.session_state:
    st.session_state.run_folding = False

# Retrieve the selected dataset from configurations (defaulting to "Quintet" if not set)
selected_dataset = st.session_state.get("table_radio", "Quintet")
datasets_path = os.path.join(os.path.dirname(__file__), "../datasets", selected_dataset)


# On first run, scan the datasets folder for subdirectories and randomly assign them to 3 initial domain folds.
if "table_locations" not in st.session_state:
    # List all subdirectories (each representing a table)
    tables = [f for f in os.listdir(datasets_path) if os.path.isdir(os.path.join(datasets_path, f))]
    folds = ["Domain Fold 1", "Domain Fold 2", "Domain Fold 3"]
    st.session_state.table_locations = {table: random.choice(folds) for table in tables}

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

# Button to start domain folding
if st.button("Run Domain Based Folding"):
    with st.spinner("🔄 Processing... Please wait..."):
        time.sleep(2)
    st.session_state.run_folding = True

if st.session_state.run_folding:
    st.markdown("---")
    
    # Group tables by their assigned fold
    domain_folds = {}
    for table, fold in st.session_state.table_locations.items():
        domain_folds.setdefault(fold, []).append(table)
    
    # HEADER: Global action buttons for merging and splitting folds
    header_cols = st.columns([4, 1, 1])
    header_cols[0].markdown("**Fold / Table**")
    if header_cols[1].button("Merge Folds", key="global_merge_button"):
        st.info("Select the Domain Folds to merge.", icon="ℹ️")
        st.session_state.merge_mode = True
        st.session_state.selected_folds = []
    if header_cols[2].button("Split Folds", key="global_split_button"):
        st.info("Select the table at which you want to split the Domain Fold. The split will occur immediately below the chosen table.", icon="ℹ️")
        st.session_state.global_split_mode = True
        st.session_state.selected_split_tables = {}
    
    st.markdown("---")
    
    # Iterate over each fold
    for fold_name, tables in domain_folds.items():
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
        
        # Display each table within the fold
        for table in tables:
            table_cols = st.columns([4, 1, 1])
            # Use an expander so that when clicked, the CSV data (clean.csv) is loaded and displayed.
            with table_cols[0].expander(f"📊 {table}"):
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
            table_cols[1].empty()
            # Global split mode: allow selecting a table to split the fold.
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
    
    # Global Confirm Merge: if merge mode is active and more than one fold is selected.
    if st.session_state.merge_mode and len(st.session_state.selected_folds) > 1:
        merge_confirm_cols = st.columns([4, 1, 1])
        if merge_confirm_cols[1].button("Confirm Merge", key="confirm_merge"):
            target_fold = st.session_state.selected_folds[0]
            for fold in st.session_state.selected_folds[1:]:
                for table in domain_folds.get(fold, []):
                    st.session_state.table_locations[table] = target_fold
            st.session_state.selected_folds = []
            st.session_state.merge_mode = False
            st.rerun()
    
    # Global Confirm Split: if split mode is active and at least one table is selected.
    if st.session_state.global_split_mode:
        any_split = any(st.session_state.selected_split_tables.get(fold, []) for fold in st.session_state.selected_split_tables)
        if any_split:
            split_confirm_cols = st.columns([4, 1, 1])
            if split_confirm_cols[2].button("Confirm Split", key="confirm_split"):
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
                st.rerun()
    
    st.markdown("---")
    
    if st.button("Next"):
        st.switch_page("pages/QualityBasedFolding.py")
