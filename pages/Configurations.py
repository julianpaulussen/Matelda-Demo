import streamlit as st
import os
import glob
import pandas as pd

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

st.title("Configurations")
st.subheader("Select a Dataset Folder")

# Determine the datasets folder relative to the current file location
datasets_folder = os.path.join(os.path.dirname(__file__), "../datasets")

# List all subfolders inside the datasets folder
dataset_options = [f for f in os.listdir(datasets_folder) if os.path.isdir(os.path.join(datasets_folder, f))]

if not dataset_options:
    st.warning("No dataset folders found in the datasets folder.")
else:
    selected_dataset_folder = st.radio(
        "Dataset Selection", 
        options=dataset_options, 
        index=0, 
        key="dataset_radio", 
        label_visibility="visible"
    )
    st.write("Selected Dataset Folder:", selected_dataset_folder)
    
    # Optional: Preview the first CSV file found in the selected folder
    folder_path = os.path.join(datasets_folder, selected_dataset_folder)
    st.write("Here is some information on the dataset.")

st.markdown("---")
st.subheader("Select Labeling Budget")

# Initialize the session state for labeling_budget if it doesn't exist.
if "labeling_budget" not in st.session_state:
    st.session_state.labeling_budget = 10

# Use the saved value (or default) for the slider.
labeling_budget = st.slider(
    "Select Labeling Budget",
    min_value=1,
    max_value=100,
    value=st.session_state.labeling_budget,
    key="budget_slider",
    label_visibility="hidden"
)

st.number_input(
    "Enter Labeling Budget",
    min_value=1,
    max_value=100,
    value=labeling_budget,
    step=1,
    key="budget_input",
    label_visibility="hidden"
)

st.markdown("---")

# Save configurations button.
if st.button("Save Configurations"):
    st.session_state.config_saved = True
    st.session_state.labeling_budget = st.session_state.budget_slider
    # Save the dataset path dynamically based on the selected dataset folder
    st.session_state.dataset_path = os.path.join(os.path.dirname(__file__), "../datasets", st.session_state.dataset_radio)
    st.success("Configurations saved!")

if st.button("Next"):
    st.switch_page("pages/DomainBasedFolding.py")
