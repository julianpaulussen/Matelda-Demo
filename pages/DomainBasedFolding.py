import streamlit as st
import pandas as pd
import numpy as np
import time

# Set the page title
st.title("Domain Based Folding")

# Initialize session state for tracking table locations
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

# Button to start processing
if st.button("Run Domain Based Folding"):
    with st.spinner("🔄 Processing... Please wait..."):
        time.sleep(3)  # Simulate a delay
    st.session_state.run_folding = True  # Show content after loading

# Show content only after clicking "Run Domain Based Folding"
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

    # Iterate through each domain fold and display tables
    for fold_name, tables in domain_folds.items():
        with st.container():
            st.subheader(f"{fold_name}")

            for table in tables:
                with st.expander(f"📊 {table}"):
                    # Show table
                    st.dataframe(generate_random_table(8, 4))

                    # Move table options (inside the same expander)
                    new_location = st.radio(
                        f"Move {table} to:",
                        options=["Domain Fold 1", "Domain Fold 2", "Domain Fold 3"],
                        index=["Domain Fold 1", "Domain Fold 2", "Domain Fold 3"].index(st.session_state.table_locations[table]),
                        key=f"move_{table}"
                    )

                    # Update session state if table is moved
                    if new_location != st.session_state.table_locations[table]:
                        st.session_state.table_locations[table] = new_location
                        st.rerun()  # Refresh to reflect changes

    # Navigation Button
    if st.button("Next"):
        st.switch_page("pages/QualityBasedFolding.py")
