import streamlit as st
import pandas as pd
import os
import json
import time
from backend_functions import backend_dbf

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

# Load dataset from pipeline config if not already in session_state
if "dataset_select" not in st.session_state and "pipeline_path" in st.session_state:
    config_path = os.path.join(st.session_state.pipeline_path, "configurations.json")
    if os.path.exists(config_path):
        with open(config_path) as f:
            config = json.load(f)
        st.session_state["dataset_select"] = config.get("selected_dataset", "Quintet")

selected_dataset = st.session_state.get("dataset_select", "Quintet")
datasets_path = os.path.join(os.path.dirname(__file__), "../datasets", selected_dataset)

# Function to load the "clean.csv" file for a given table
def load_clean_table(table_name):
    file_path = os.path.join(datasets_path, table_name, "clean.csv")
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        df = pd.DataFrame({"Error": [f"Could not load {file_path}: {e}"]})
    return df

# Initialize the run_complete state if not exists
if "run_complete" not in st.session_state:
    st.session_state.run_complete = False

# Button to start domain folding
if st.button("▶️ Run Domain Based Folding"):
    with st.spinner("🔄 Processing... Please wait..."):
        # Add a 1-second delay for the loading animation
        time.sleep(1)
        
        # Call the backend function
        result = backend_dbf(selected_dataset, labeling_budget=100)  # You might want to make labeling_budget configurable
        
        # Save the results to configurations.json
        if "pipeline_path" in st.session_state:
            config_path = os.path.join(st.session_state.pipeline_path, "configurations.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)
            else:
                config = {}
            
            config.update(result)
            
            with open(config_path, "w") as f:
                json.dump(config, f, indent=4)
            
            st.success("Domain folds have been generated and saved!")
            # Set run_complete to True after successful execution
            st.session_state.run_complete = True
        else:
            st.warning("No pipeline selected; domain folds not saved.")

# Display the current domain folds if they exist
if "pipeline_path" in st.session_state:
    config_path = os.path.join(st.session_state.pipeline_path, "configurations.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = json.load(f)
        
        if "domain_folds" in config:
            st.markdown("## Current Domain Folds")
            for fold_name, tables in config["domain_folds"].items():
                st.markdown(f"### {fold_name}")
                for table in tables:
                    with st.expander(f"📊 {table}"):
                        df = load_clean_table(table)
                        st.dataframe(df)

# Only show the Next button after running the folding process
if st.session_state.run_complete:
    if st.button("Next"):
        st.switch_page("pages/QualityBasedFolding.py")
