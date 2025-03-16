import streamlit as st
import pandas as pd
import numpy as np
import time

# Set the page title and layout
st.set_page_config(page_title="Detected Errors", layout="wide")
st.title("Detected Errors")

# List of tables
tables = [
    "Sales Data",
    "Customer Data",
    "Inventory Data",
    "Financial Report",
    "Employee Data",
    "Performance Metrics",
    "Risk Analysis"
]

    
if "run_error_detection" not in st.session_state:
    st.session_state.run_error_detection = False  

if st.button("Run Error Detection"):
    with st.spinner("🔄 Detecting errors... Please wait..."):
        time.sleep(3)  # Simulate processing delay
    st.session_state.run_error_detection = True
    st.rerun()  # Refresh to show tables

# Function to generate a random table with errors
def generate_table_with_errors(rows=8, cols=4):
    df = pd.DataFrame(
        np.random.randint(1, 100, size=(rows, cols)), 
        columns=[f"Col {i+1}" for i in range(cols)]
    )

    # Randomly select error positions
    num_errors = np.random.randint(2, 6)
    error_positions = {(np.random.randint(0, rows), np.random.randint(0, cols)) for _ in range(num_errors)}

    # Define function to highlight errors
    def highlight_errors(data):
        df_styles = pd.DataFrame("", index=data.index, columns=data.columns)
        for row, col in error_positions:
            df_styles.iloc[row, col] = "background-color: red; color: white"
        return df_styles

    return df.style.apply(highlight_errors, axis=None)

# If errors have been detected, show tables
if st.session_state.run_error_detection:
    st.markdown("---")
    
    for table in tables:
        with st.expander(f"📊 {table} (Errors Highlighted)"):
            st.dataframe(generate_table_with_errors())

    st.markdown("---")

    # Navigation button to Results page
    if st.button("Next"):
        st.switch_page("pages/Results.py")
