import streamlit as st
import pandas as pd
import numpy as np
import time

# Set the page title
st.set_page_config(page_title="Domain Based Folding", layout="wide")

st.title("Domain Based Folding")

# Initialize session state variables
if "run_folding" not in st.session_state:
    st.session_state.run_folding = False  # Controls when tables are shown

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
    st.session_state.merge_mode = False  # Enables checkboxes for merging

if "selected_folds" not in st.session_state:
    st.session_state.selected_folds = []  # Stores selected folds for merging

if "split_mode" not in st.session_state:
    st.session_state.split_mode = {}  # Tracks active splits per fold

if "selected_split_tables" not in st.session_state:
    st.session_state.selected_split_tables = {}  # Tracks selected tables per fold for splitting

# Button to start processing
if st.button("Run Domain Based Folding"):
    with st.spinner("🔄 Processing... Please wait..."):
        time.sleep(2)  # Simulate a delay
    st.session_state.run_folding = True  # Show tables

# Only show content after clicking "Run Domain Based Folding"
if st.session_state.run_folding:

    st.markdown("---")

    # Function to generate a random table
    def generate_random_table(rows=5, cols=4):
        return pd.DataFrame(
            np.random.randint(1, 100, size=(rows, cols)), 
            columns=[f"Col {i+1}" for i in range(cols)]
        )

    # Folds Dictionary
    domain_folds = {}
    for table, fold in st.session_state.table_locations.items():
        if fold not in domain_folds:
            domain_folds[fold] = []
        domain_folds[fold].append(table)

    # Enable merge mode
    if st.button("Merge Domain Folds"):
        st.session_state.merge_mode = True  # Show checkboxes
        st.session_state.selected_folds = []  # Reset selection

    # Display domain folds
    for fold_name, tables in domain_folds.items():
        cols = st.columns([4, 1, 1])  # Three columns: fold name, split button, merge checkboxes

        with cols[0]:  
            st.subheader(f"{fold_name}")  # Show fold name

        # Split Button
        with cols[1]:  
            if st.button("Split", key=f"split_btn_{fold_name}"):
                st.session_state.split_mode[fold_name] = True
                st.session_state.selected_split_tables[fold_name] = []  # Reset selection

        # Merge Checkboxes (if merge mode is active)
        with cols[2]:  
            if st.session_state.merge_mode:  
                selected = st.checkbox("Select Fold to Merge", key=f"checkbox_{fold_name}", label_visibility="hidden")
                if selected and fold_name not in st.session_state.selected_folds:
                    st.session_state.selected_folds.append(fold_name)
                elif not selected and fold_name in st.session_state.selected_folds:
                    st.session_state.selected_folds.remove(fold_name)

        # Display tables within the fold
        valid_split = False  # Track if a valid split exists
        selected_indices = []  # Store indices of selected tables

        for i, table in enumerate(tables):
            cols_table = st.columns([4, 1])  

            with cols_table[0]:  
                with st.expander(f"📊 {table}"):
                    st.dataframe(generate_random_table(8, 4))

                    # Move table (Only visible when the table expander is opened)
                    new_location = st.radio(
                        f"Move {table} to:",
                        options=list(domain_folds.keys()),
                        index=list(domain_folds.keys()).index(st.session_state.table_locations[table]),
                        key=f"move_{table}"
                    )

                    # Update session state if table is moved
                    if new_location != st.session_state.table_locations[table]:
                        st.session_state.table_locations[table] = new_location
                        st.rerun()  # Refresh to reflect changes

            # Split checkboxes (only show when split mode is active for this fold)
            with cols_table[1]:  
                if st.session_state.split_mode.get(fold_name, False):
                    selected_tables = st.session_state.selected_split_tables[fold_name]

                    selected = st.checkbox("Split here", key=f"split_checkbox_{fold_name}_{table}", label_visibility="hidden")
                    
                    if selected and table not in selected_tables:
                        if len(selected_tables) == 1:
                            prev_index = tables.index(selected_tables[0])
                            if abs(prev_index - i) == 1:  # Check adjacency
                                selected_tables.append(table)
                                selected_indices = [prev_index, i]  # Store valid split indices
                                valid_split = True
                            else:
                                selected_tables.pop(0)  # Remove first selection if non-adjacent
                                selected_tables.append(table)
                        else:
                            selected_tables.append(table)

                    elif not selected and table in selected_tables:
                        selected_tables.remove(table)

        # Show Confirm Split Button ONLY if exactly 2 tables are selected for splitting and they are adjacent
        if fold_name in st.session_state.selected_split_tables and len(st.session_state.selected_split_tables[fold_name]) == 2:
            selected_tables = st.session_state.selected_split_tables[fold_name]
            # Calculate indices for the selected tables within the current fold
            indices = [tables.index(t) for t in selected_tables if t in tables]
            indices.sort()
            # Check if the selected tables are adjacent
            if indices[1] - indices[0] == 1:
                if st.button(f"Confirm Split {fold_name}", key=f"confirm_split_{fold_name}"):
                    new_fold_name = f"{fold_name} - Split {len(domain_folds) + 1}"
                    # Move the second table and all tables after it to the new fold
                    for table in tables[indices[1]:]:
                        st.session_state.table_locations[table] = new_fold_name

                    # Reset the split mode and clear the selection
                    st.session_state.split_mode[fold_name] = False
                    st.session_state.selected_split_tables[fold_name] = []
                    st.rerun()




    # Floating merge confirmation button
    if len(st.session_state.selected_folds) > 1:
        st.markdown('<div class="fixed-bottom">', unsafe_allow_html=True)
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if st.button("Confirm Merge"):
                target_fold = st.session_state.selected_folds[0]  

                for fold in st.session_state.selected_folds[1:]:
                    for table in domain_folds[fold]:
                        st.session_state.table_locations[table] = target_fold
                
                st.session_state.selected_folds = []
                st.session_state.merge_mode = False
                
                st.rerun()
                
        st.markdown('</div>', unsafe_allow_html=True)

    # Navigation Button
    st.markdown("---")

    if st.button("Next"):
        st.switch_page("pages/QualityBasedFolding.py")
