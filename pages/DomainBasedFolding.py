import streamlit as st
import pandas as pd
import numpy as np
import time  # For simulating loading time

# Set the page title
st.title("Domain Based Folding")

# Initialize session state
if "run_folding" not in st.session_state:
    st.session_state.run_folding = False

# Button to start processing
if st.button("Run Domain Based Folding"):
    with st.spinner("🔄 Processing... Please wait..."):  # Show loading animation
        time.sleep(5)  # Simulate a delay
    st.session_state.run_folding = True  # Show content after loading

# Show content only after clicking "Run Domain Based Folding"
if st.session_state.run_folding:

    # Function to generate a random table
    def generate_random_table(rows=5, cols=4):
        return pd.DataFrame(
            np.random.randint(1, 100, size=(rows, cols)), 
            columns=[f"Col {i+1}" for i in range(cols)]
        )

    # FIRST CONTAINER: 3 Tables
    with st.container():
        st.subheader("Domain Fold 1")

        with st.expander("Sales Data"):
            st.dataframe(generate_random_table(10, 5))

        with st.expander("Customer Data"):
            st.dataframe(generate_random_table(8, 4))

        with st.expander("Inventory Data"):
            st.dataframe(generate_random_table(12, 6))

    # SECOND CONTAINER: 2 Tables
    with st.container():
        st.subheader("Domain Fold 2")

        with st.expander("Financial Report"):
            st.dataframe(generate_random_table(7, 4))

        with st.expander("Employee Data"):
            st.dataframe(generate_random_table(9, 5))

    # THIRD CONTAINER: 2 Tables
    with st.container():
        st.subheader("Domain Fold 3")

        with st.expander("Performance Metrics"):
            st.dataframe(generate_random_table(6, 3))

        with st.expander("Risk Analysis"):
            st.dataframe(generate_random_table(5, 4))

    # Navigation Button
    if st.button("Next"):
        st.switch_page("pages/QualityBasedFolding.py")
