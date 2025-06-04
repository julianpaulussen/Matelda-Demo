import streamlit as st
import os
import json
import pandas as pd
import zipfile
import shutil

# Hide default Streamlit menu
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] {display: none;}
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.page_link("app.py", label="Matelda")
    st.page_link("pages/Configurations.py", label="Configurations")
    st.page_link("pages/DomainBasedFolding.py", label="Domain Based Folding")
    st.page_link("pages/QualityBasedFolding.py", label="Quality Based Folding")
    st.page_link("pages/Labeling.py", label="Labeling")
    st.page_link("pages/ErrorDetection.py", label="Error Detection")
    st.page_link("pages/Results.py", label="Results")

st.title("Configurations")

# ----------------------------
# Pipeline Selection Section
# ----------------------------
pipelines_folder = os.path.join(os.path.dirname(__file__), "../pipelines")
if not os.path.exists(pipelines_folder):
    os.makedirs(pipelines_folder)

existing_pipelines = [f for f in os.listdir(pipelines_folder) if os.path.isdir(os.path.join(pipelines_folder, f))]
placeholder = "Click here to select existing pipeline"

# Initialize state for new pipeline validation
if "valid_pipeline_name" not in st.session_state:
    st.session_state.valid_pipeline_name = True


def load_pipeline_config():
    """
    Load labeling budget and dataset from the selected pipeline's configuration JSON.
    Additionally, if a dataset is already selected in the UI (via st.session_state.dataset_select),
    compare it to the one stored in the configuration. If they match, update the labeling budget
    to the actual saved value.
    """
    selected = st.session_state.selected_pipeline
    # Do nothing if the placeholder is still selected.
    if selected == placeholder:
        return
    pipeline_config_path = os.path.join(pipelines_folder, selected, "configurations.json")
    if os.path.exists(pipeline_config_path):
        with open(pipeline_config_path, "r") as f:
            pipeline_config = json.load(f)
        pipeline_dataset = pipeline_config.get("selected_dataset", None)
        # Get the dataset currently selected in the UI (from the selectbox, which writes to st.session_state.dataset_select)
        current_dataset = st.session_state.get("dataset_select")
        if current_dataset is None and pipeline_dataset:
            st.session_state["dataset_select"] = pipeline_dataset
            current_dataset = pipeline_dataset
        # Update the budget regardless
        st.session_state.budget_slider = pipeline_config.get("labeling_budget", 10)
        st.session_state.preconfigured_dataset = pipeline_dataset
    else:
        st.session_state.budget_slider = 10
        st.session_state.preconfigured_dataset = "Not defined"

pipeline_choice = st.radio(
    "Do you want to use an existing pipeline or create a new one?",
    options=["Create New Pipeline", "Use Existing Pipeline"],
    index=0,
)

if pipeline_choice == "Use Existing Pipeline":
    # Show placeholder first, then existing pipelines.
    pipeline_options = [placeholder] + existing_pipelines
    selected_pipeline = st.selectbox(
        "Select an existing pipeline:", 
        options=pipeline_options, 
        key="selected_pipeline",
        on_change=load_pipeline_config
    )
    
    # On first load, load configuration if not already set.
    if "budget_slider" not in st.session_state:
        load_pipeline_config()
    
    st.markdown("---")
    st.subheader("Labeling Budget")
    current_budget = st.session_state.get("budget_slider", 10)
    labeling_budget = st.slider(
        "Select Labeling Budget:",
        min_value=1,
        max_value=100,
        value=current_budget,
        label_visibility="visible",
    )
    st.number_input(
        "Enter Labeling Budget",
        min_value=1,
        max_value=100,
        value=labeling_budget,
        step=1,
        key="budget_input",
        label_visibility="hidden",
    )
    st.session_state.budget_slider = labeling_budget
else:
    # ----------------------------
    # Create New Pipeline: Dataset & Budget Selection
    # ----------------------------

    st.markdown("---")
    st.subheader("Dataset Selection")

    # 1) Make sure "../datasets" exists
    datasets_folder = os.path.join(os.path.dirname(__file__), "../datasets")
    if not os.path.exists(datasets_folder):
        os.makedirs(datasets_folder)

    # 2) Initialize our session_state buckets (only happens once)
    if "processed_file_ids" not in st.session_state:
        # Track which uploaded files we've already extracted in this session
        st.session_state["processed_file_ids"] = set()

    if "uploaded_dataset_name" not in st.session_state:
        # This will hold the most recently uploaded folder-name
        st.session_state["uploaded_dataset_name"] = None

    # 3) File uploader (always visible)
    st.markdown("##### Add Dataset (optional)")
    uploaded_file = st.file_uploader(
        "Upload a zip file containing the dataset:", 
        type=["zip"], 
        key="dataset_zip_uploader",
    )

    # 4) If the user has picked a new ZIP, extract it once per unique file upload
    if uploaded_file is not None:
        file_id = getattr(uploaded_file, "id", None)
        if file_id is None:
            file_id = getattr(uploaded_file, "file_id", None)
        if file_id is None:
            file_id = id(uploaded_file)
        if file_id not in st.session_state["processed_file_ids"]:
            # Start extraction
            status = st.empty()
            with st.spinner("Uploading and extracting…"):
                status.text("Uploading…")
                zip_filename = uploaded_file.name
                base_name = os.path.splitext(zip_filename)[0]
                with zipfile.ZipFile(uploaded_file, "r") as zip_ref:
                    entries = [info.filename for info in zip_ref.infolist() if info.filename and not info.filename.startswith("__MACOSX/")]
                    top_dirs = {entry.split("/", 1)[0] for entry in entries}
                    if len(top_dirs) == 1:
                        inner_root = next(iter(top_dirs))
                        dataset_base = inner_root.rstrip("/")
                    else:
                        dataset_base = base_name

                    new_dataset_path = os.path.join(datasets_folder, dataset_base)

                    # Auto‐increment if folder already exists
                    counter = 1
                    dataset_name = dataset_base
                    while os.path.exists(new_dataset_path):
                        dataset_name = f"{dataset_base}_{counter}"
                        new_dataset_path = os.path.join(datasets_folder, dataset_name)
                        counter += 1

                    os.makedirs(new_dataset_path, exist_ok=True)
                    status.text("Extracting…")
                    if len(top_dirs) == 1:
                        for member in zip_ref.infolist():
                            member_name = member.filename
                            if member_name.startswith(inner_root):
                                member_name = member_name[len(inner_root):].lstrip("/")
                            if not member_name:
                                continue
                            target_path = os.path.join(new_dataset_path, member_name)
                            if member.is_dir():
                                os.makedirs(target_path, exist_ok=True)
                            else:
                                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                                with zip_ref.open(member) as src, open(target_path, "wb") as dst:
                                    shutil.copyfileobj(src, dst)
                    else:
                        zip_ref.extractall(new_dataset_path)
                status.text("Cleaning up…")
                status.empty()

            # Remember that we extracted this one, and record the created folder-name
            st.session_state["processed_file_ids"].add(file_id)
            # Record only the latest uploaded dataset so previous
            # notifications can be cleared on subsequent uploads
            st.session_state["uploaded_dataset_name"] = dataset_name

    # 5) Show a persistent notification for the most recently uploaded dataset
    if st.session_state.get("uploaded_dataset_name"):
        st.success(f"Added new dataset: {st.session_state['uploaded_dataset_name']}")

    # 6) Now list all folders under "../datasets" (including ones you uploaded previously,
    #    plus any that already existed on disk before you ran this app).
    st.markdown("##### Select Dataset")
    
    dataset_options = [
        d
        for d in os.listdir(datasets_folder)
        if os.path.isdir(os.path.join(datasets_folder, d))
    ]
    if not dataset_options:
        st.warning("No dataset folders found in the datasets folder.")
    else:
        selected_dataset_folder = st.selectbox(
            "Select the dataset you want to use:",
            options=dataset_options,
            key="dataset_select",
            label_visibility="visible"
        )
        st.write(f"Here is some information about the selected dataset: `Insert Information`")


    st.markdown("---")
    st.subheader("Labeling Budget")
    labeling_budget = st.slider(
        "Select Labeling Budget:",
        min_value=1,
        max_value=100,
        value=st.session_state.get("budget_slider", 10),
        label_visibility="visible",
    )
    st.number_input(
        "Enter Labeling Budget",
        min_value=1,
        max_value=100,
        value=labeling_budget,
        step=1,
        key="budget_input",
        label_visibility="hidden",
    )
    st.session_state.budget_slider = labeling_budget
    
    # ----------------------------
    # Suggest Unique Pipeline Folder Name at the Bottom
    # ----------------------------
    def suggest_pipeline_folder_name(dataset_name, pipelines_dir):
        """
        Suggests a unique pipeline folder name in the format:
        {dataset_name}-pipeline-{number:02d}
        """
        candidate_prefix = f"{dataset_name}-pipeline-"
        candidates = [
            d for d in os.listdir(pipelines_dir)
            if os.path.isdir(os.path.join(pipelines_dir, d)) and d.startswith(candidate_prefix)
        ]
        if not candidates:
            return f"{dataset_name}-pipeline-01"
        else:
            max_num = 0
            for d in candidates:
                try:
                    num = int(d.replace(candidate_prefix, ""))
                    if num > max_num:
                        max_num = num
                except:
                    continue
            next_num = max_num + 1
            return f"{dataset_name}-pipeline-{next_num:02d}"
    
    st.markdown("---")
    st.subheader("Pipeline Name")
    default_pipeline_name = suggest_pipeline_folder_name(st.session_state.get("dataset_select", "dataset"), pipelines_folder)
    new_pipeline_name = st.text_input(
        "Enter a new pipeline name:", 
        value=default_pipeline_name,
        key="new_pipeline_name"
    )
    # Real-time validation for existing pipeline name
    if new_pipeline_name:
        new_folder_path = os.path.join(pipelines_folder, new_pipeline_name)
        if os.path.exists(new_folder_path):
            st.warning("A pipeline with that name already exists. Please choose a different name.")
            st.session_state.valid_pipeline_name = False
        else:
            st.session_state.valid_pipeline_name = True

# ----------------------------
# Helper Functions for Saving Configurations
# ----------------------------

def save_config_to_json(config, folder):
    """Saves the configuration dictionary as configurations.json inside the specified folder."""
    config_path = os.path.join(folder, "configurations.json")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)

# ----------------------------
# Save and Continue Button
# ----------------------------
if st.button("Save and Continue"):
    if pipeline_choice == "Use Existing Pipeline":
        # Check if the placeholder is still selected
        if st.session_state.selected_pipeline == placeholder:
            st.warning("Please select an existing pipeline before continuing.")
        else:
            pipeline_folder = os.path.join(pipelines_folder, st.session_state.selected_pipeline)
            st.session_state.pipeline_path = pipeline_folder
            pipeline_config_path = os.path.join(pipeline_folder, "configurations.json")
            config_to_save = {}
            if os.path.exists(pipeline_config_path):
                with open(pipeline_config_path, "r") as f:
                    config_to_save = json.load(f)
            config_to_save["labeling_budget"] = st.session_state.get("budget_slider", labeling_budget)
            config_to_save["selected_dataset"] = st.session_state.get("dataset_select")
            with open(pipeline_config_path, "w") as f:
                json.dump(config_to_save, f, indent=4)
            st.success(f"Configurations updated in existing pipeline: {pipeline_folder}!")
            st.switch_page("pages/DomainBasedFolding.py")
    else:
        # Create New Pipeline: Check for existing folder name
        if not new_pipeline_name:
            st.warning("Please enter a pipeline name.")
        elif not st.session_state.valid_pipeline_name:
            st.warning("Cannot save: pipeline name already exists.")
        else:
            new_folder_path = os.path.join(pipelines_folder, new_pipeline_name)
            os.makedirs(new_folder_path)
            pipeline_folder = new_folder_path
            st.session_state.pipeline_path = pipeline_folder
            config_to_save = {
                "selected_dataset": st.session_state.get("dataset_select"),
                "labeling_budget": st.session_state.get("budget_slider", labeling_budget),
            }
            save_config_to_json(config_to_save, pipeline_folder)
            st.success(f"New pipeline created and configurations saved in {pipeline_folder}!")
            st.switch_page("pages/DomainBasedFolding.py")
