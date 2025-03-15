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
    st.session_state.merge_mode = False  # Enables checkboxes

if "selected_folds" not in st.session_state:
    st.session_state.selected_folds = []  # Stores selected folds for merging

# Button to start processing
if st.button("Run Domain Based Folding"):
    with st.spinner("🔄 Processing... Please wait..."):
        time.sleep(2)  # Simulate a delay
    st.session_state.run_folding = True  # Show tables

# Only show content after clicking "Run Domain Based Folding"
if st.session_state.run_folding:

    # Function to generate a random table
    def generate_random_table(rows=5, cols=4):
        return pd.DataFrame(
            np.random.randint(1, 100, size=(rows, cols)), 
            columns=[f"Col {i+1}" for i in range(cols)]
        )

    # Folds Dictionary
    domain_folds = {
        "Domain Fold 1": [],
        "Domain Fold 2": [],
        "Domain Fold 3": []
    }

    # Sort tables into their current domain fold
    for table_name, fold in st.session_state.table_locations.items():
        domain_folds[fold].append(table_name)

    # Floating merge confirmation button
    st.markdown("""
        <style>
            .fixed-bottom {
                position: fixed;
                bottom: 0;
                left: 0;
                width: 100%;
                background-color: rgba(0, 0, 0, 0.9);
                color: white;
                text-align: center;
                padding: 15px;
                font-size: 18px;
                font-weight: bold;
                z-index: 1000;
            }
            .checkbox-column {
                display: flex;
                justify-content: flex-end;
                align-items: center;
            }
        </style>
    """, unsafe_allow_html=True)

    # Enable merge mode
    if st.button("Merge Domain Folds"):
        st.session_state.merge_mode = True  # Show checkboxes
        st.session_state.selected_folds = []  # Reset selection

    # Display domain folds
    for fold_name, tables in domain_folds.items():
        cols = st.columns([4, 1])  # Two columns: left for name, right for checkbox

        with cols[0]:  
            st.subheader(f"{fold_name}")  # Show fold name
        
        with cols[1]:  
            if st.session_state.merge_mode:  # Show checkboxes if merge mode is active
                selected = st.checkbox("", key=f"checkbox_{fold_name}")
                if selected and fold_name not in st.session_state.selected_folds:
                    st.session_state.selected_folds.append(fold_name)
                elif not selected and fold_name in st.session_state.selected_folds:
                    st.session_state.selected_folds.remove(fold_name)

        # Show tables under each fold
        for table in tables:
            with st.expander(f"📊 {table}"):
                st.dataframe(generate_random_table(8, 4))

    # Floating merge confirmation button
    if len(st.session_state.selected_folds) > 1:
        st.markdown('<div class="fixed-bottom">', unsafe_allow_html=True)
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if st.button("Confirm Merge"):
                # Perform fold merge
                target_fold = st.session_state.selected_folds[0]  # First selected fold
                
                # Move tables from all selected folds into the first one
                for fold in st.session_state.selected_folds[1:]:
                    for table in domain_folds[fold]:
                        st.session_state.table_locations[table] = target_fold
                
                # Clear selections
                st.session_state.selected_folds = []
                st.session_state.merge_mode = False
                
                # Refresh page
                st.rerun()
                
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Navigation Button
    if st.button("Next"):
        st.switch_page("pages/QualityBasedFolding.py")
