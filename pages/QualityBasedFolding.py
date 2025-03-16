import streamlit as st
import pandas as pd
import numpy as np
import time

# Set page title and layout
st.set_page_config(page_title="Quality Based Folding", layout="wide")
st.title("Quality Based Folding")

# Initialize session state
if "run_quality_folding" not in st.session_state:
    st.session_state.run_quality_folding = False

if st.button("Run Quality Based Folding"):
  with st.spinner("🔄 Processing... Please wait..."):
    time.sleep(3)  # Simulate delay
  st.session_state.run_quality_folding = True
  st.rerun()  # Refresh to show the tables

# Function to generate random table data
def generate_random_table(rows=6, cols=4):
    return pd.DataFrame(
        np.random.randint(1, 100, size=(rows, cols)), 
        columns=[f"Col {i+1}" for i in range(cols)]
    )

# If the button has been clicked, show the fold structure
if st.session_state.run_quality_folding:
    st.markdown("---")

    # Simulated domain-based folds (imported from session state)
    if "table_locations" in st.session_state:
        domain_folds = {}
        for table, fold in st.session_state.table_locations.items():
            domain_folds.setdefault(fold, []).append(table)
    else:
        # Default structure if session state is missing
        domain_folds = {
            "Domain Fold 1": ["Sales Data", "Customer Data", "Inventory Data"],
            "Domain Fold 2": ["Financial Report", "Employee Data"],
            "Domain Fold 3": ["Performance Metrics", "Risk Analysis"]
        }

    # Iterate over each domain fold
    for fold_name, tables in domain_folds.items():
        st.subheader(f"{fold_name}")  # Domain fold as a section header
        for table in tables:
            with st.expander(f"Quality Based Cell Fold: {table}"):
                st.dataframe(generate_random_table(6, 4))  # Show random table data

    st.markdown("---")

    # Navigation button to the Labeling page
    if st.button("Next"):
        st.switch_page("pages/Labeling.py")
