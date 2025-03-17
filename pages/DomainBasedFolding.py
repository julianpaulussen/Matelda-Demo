import streamlit as st
import pandas as pd
import numpy as np
import time

# Set the page title and layout
st.set_page_config(page_title="Domain Based Folding", layout="wide")
st.title("Domain Based Folding")

# Hide default Streamlit menu
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.page_link("app.py", label="Matelda")
    st.page_link("pages/Configurations.py", label="Configurations")
    st.page_link("pages/DomainBasedFolding.py", label="Domain Based Folding")
    st.page_link("pages/QualityBasedFolding.py", label="Quality Based Folding")
    st.page_link("pages/Labeling.py", label="Labeling")
    st.page_link("pages/ErrorDetection.py", label="Error Detection")
    st.page_link("pages/Results.py", label="Results")

# Initialize session state variables
if "run_folding" not in st.session_state:
    st.session_state.run_folding = False  

if "table_locations" not in st.session_state:
    st.session_state.table_locations = {
        "Sales Data": "Domain Fold 1",
        "Customer Data": "Domain Fold 1",
        "Inventory Data": "Domain Fold 1",
        "Financial Report": "Domain Fold 2",
        "Employee Data": "Domain Fold 2",
        "Performance Metrics": "Domain Fold 3",
        "Risk Analysis": "Domain Fold 3"
    }

if "merge_mode" not in st.session_state:
    st.session_state.merge_mode = False  

if "selected_folds" not in st.session_state:
    st.session_state.selected_folds = []  

# Global split mode (for tables across folds)
if "global_split_mode" not in st.session_state:
    st.session_state.global_split_mode = False  

if "selected_split_tables" not in st.session_state:
    # This will be a dict with key = fold name, value = list of table names selected for splitting
    st.session_state.selected_split_tables = {}  

# Button to start processing
if st.button("Run Domain Based Folding"):
    with st.spinner("🔄 Processing... Please wait..."):
        time.sleep(2)  
    st.session_state.run_folding = True  

if st.session_state.run_folding:
    st.markdown("---")
    
    # Function to generate a random table for display
    def generate_random_table(rows=5, cols=4):
        return pd.DataFrame(
            np.random.randint(1, 100, size=(rows, cols)), 
            columns=[f"Col {i+1}" for i in range(cols)]
        )
    
    # Group tables by their fold
    domain_folds = {}
    for table, fold in st.session_state.table_locations.items():
        domain_folds.setdefault(fold, []).append(table)
    
    # HEADER ROW with global action buttons
    header_cols = st.columns([4, 1, 1])
    header_cols[0].markdown("**Fold / Table**")
    # Global Merge button: when clicked, enable merge mode
    if header_cols[1].button("Merge Folds", key="global_merge_button"):
        st.info("Select the Domain Folds to merge.", icon="ℹ️")
        st.session_state.merge_mode = True
        st.session_state.selected_folds = []
    # Global Split button: when clicked, enable global split mode
    if header_cols[2].button("Split Folds", key="global_split_button"):
        st.info("Select the table at which you want to split the Domain Fold. The split will occur immediately below the chosen table.", icon="ℹ️")
        st.session_state.global_split_mode = True
        st.session_state.selected_split_tables = {}
    
    st.markdown("---")
    
    # Iterate over each fold
    for fold_name, tables in domain_folds.items():
        # Row for the fold name with merge checkbox if merge mode is active
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
        # (For fold rows we do not need a split button now; split is handled globally.)
        fold_cols[2].empty()
        
        # Now add a row for each table in this fold
        for table in tables:
            table_cols = st.columns([4, 1, 1])
            # Left column: an expander with the table and a radio to move it if desired
            with table_cols[0].expander(f"📊 {table}"):
                st.dataframe(generate_random_table(8, 4))
                new_location = st.radio(
                    f"Move {table} to:",
                    options=list(domain_folds.keys()),
                    index=list(domain_folds.keys()).index(st.session_state.table_locations[table]),
                    key=f"move_{table}"
                )
                if new_location != st.session_state.table_locations[table]:
                    st.session_state.table_locations[table] = new_location
                    st.rerun()
            # Middle column: no merge control on table rows
            table_cols[1].empty()
            # Right column: if global split mode is active, show a split checkbox
            if st.session_state.global_split_mode:
                split_selected = table_cols[2].checkbox("Split here", key=f"split_{fold_name}_{table}", label_visibility="hidden")
                # Initialize the list for this fold if not already
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
        if merge_confirm_cols[1].button("Confirm Merge", key="confirm_merge"):
            target_fold = st.session_state.selected_folds[0]
            for fold in st.session_state.selected_folds[1:]:
                for table in domain_folds.get(fold, []):
                    st.session_state.table_locations[table] = target_fold
            st.session_state.selected_folds = []
            st.session_state.merge_mode = False
            st.rerun()
    
    # Global Confirm Split if global split mode is active and at least one table is selected
    if st.session_state.global_split_mode:
        # Check if at least one table is selected for splitting
        any_split = any(st.session_state.selected_split_tables.get(fold, []) for fold in st.session_state.selected_split_tables)
        if any_split:
            split_confirm_cols = st.columns([4, 1, 1])
            if split_confirm_cols[2].button("Confirm Split", key="confirm_split"):
                # Process splits fold by fold
                for fold_name, selected_tables in st.session_state.selected_split_tables.items():
                    if selected_tables:
                        # Get the list of tables currently in this fold (in their display order)
                        tables_in_fold = domain_folds.get(fold_name, [])
                        # Find the indices of selected tables (sorted)
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
