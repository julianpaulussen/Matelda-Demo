import streamlit as st
import random
import os
import json
import datetime
import pandas as pd
import urllib.parse
from components import render_sidebar, apply_base_styles

# Set page config and apply base styles
st.set_page_config(page_title="Results", layout="wide")
apply_base_styles()

# Sidebar navigation
render_sidebar()

st.title("Results")
st.write("### Model Performance Metrics")

def load_config(path):
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

if "pipeline_path" in st.session_state:
    current_pipeline_path = st.session_state.pipeline_path
    config_path = os.path.join(current_pipeline_path, "configurations.json")
    config = load_config(config_path)
    results = config.get("results", [])

    if results:
        latest_result = results[-1]
        metrics = latest_result.get("metrics", {})
        recall_score = metrics.get("Recall", 0)
        f1_score = metrics.get("F1", 0)
        precision_score = metrics.get("Precision", 0)
        current_time = latest_result.get("Time", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    else:
        recall_score = 0
        f1_score = 0
        precision_score = 0
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
else:
    st.error("No pipeline selected!")
    st.stop()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Recall", value=f"{recall_score:.2f}")
with col2:
    st.metric(label="F1 Score", value=f"{f1_score:.2f}")
with col3:
    st.metric(label="Precision", value=f"{precision_score:.2f}")

# -----------------------------------------------------------------------------
# Ensure that the current dataset is defined in session state.
# -----------------------------------------------------------------------------
current_dataset = st.session_state.get("dataset_select", None)
if not current_dataset and "pipeline_path" in st.session_state:
    cfg = load_config(os.path.join(st.session_state.pipeline_path, "configurations.json"))
    current_dataset = cfg.get("selected_dataset", None)
    if current_dataset:
        st.session_state.dataset_select = current_dataset

if not current_dataset:
    st.warning("No dataset defined in session state.")
    st.stop()

current_pipeline_name = os.path.basename(current_pipeline_path)
pipelines_folder = os.path.join(os.path.dirname(__file__), "../pipelines")

same_dataset_rows = []
for pipeline in os.listdir(pipelines_folder):
    pipeline_dir = os.path.join(pipelines_folder, pipeline)
    if os.path.isdir(pipeline_dir):
        cfg = load_config(os.path.join(pipeline_dir, "configurations.json"))
        if cfg.get("selected_dataset") == current_dataset:
            labeling_budget = cfg.get("labeling_budget", "")
            results_list = cfg.get("results", [])
            for res in results_list:
                metrics = res.get("metrics", {})
                row = {
                    "Time": res.get("Time", ""),
                    "Pipeline Name": pipeline,
                    "Labeling Budget": labeling_budget,
                    "Recall": metrics.get("Recall", ""),
                    "F1": metrics.get("F1", ""),
                    "Precision": metrics.get("Precision", "")
                }
                same_dataset_rows.append(row)

found_current = any(
    row["Pipeline Name"] == current_pipeline_name and row["Time"] == current_time
    for row in same_dataset_rows
)
if not found_current:
    current_cfg = load_config(os.path.join(current_pipeline_path, "configurations.json"))
    current_labeling_budget = current_cfg.get("labeling_budget", "")
    current_row = {
        "Time": current_time,
        "Pipeline Name": current_pipeline_name,
        "Labeling Budget": current_labeling_budget,
        "Recall": recall_score,
        "F1": f1_score,
        "Precision": precision_score
    }
    # Remove duplicates for today from same pipeline
    same_dataset_rows = [
        r for r in same_dataset_rows
        if not (r["Pipeline Name"] == current_pipeline_name and r["Time"].split(" ")[0] == current_time.split(" ")[0])
    ]
    same_dataset_rows.append(current_row)

same_dataset_df = pd.DataFrame(same_dataset_rows)
for col in ["Recall", "F1", "Precision", "Labeling Budget"]:
    if col in same_dataset_df.columns:
        same_dataset_df[col] = pd.to_numeric(same_dataset_df[col], errors="coerce").round(2)
same_dataset_df = same_dataset_df.sort_values(by="Time", ascending=False)

def highlight_current(row):
    if row["Pipeline Name"] == current_pipeline_name and row["Time"] == current_time:
        return ['background-color: red'] * len(row)
    else:
        return [''] * len(row)

styled_same_dataset_df = same_dataset_df.style.apply(highlight_current, axis=1).format({
    "Recall": "{:.2f}",
    "F1": "{:.2f}",
    "Precision": "{:.2f}",
    "Labeling Budget": "{:}"
})

st.markdown("---")
st.markdown(f"#### Result Comparison (Dataset: {current_dataset}):")
st.write("_(Click on column headers to sort the table.)_")
st.dataframe(styled_same_dataset_df)

# ---------------- ALL DATASETS ----------------
all_rows = []
for pipeline in os.listdir(pipelines_folder):
    pipeline_dir = os.path.join(pipelines_folder, pipeline)
    if os.path.isdir(pipeline_dir):
        cfg = load_config(os.path.join(pipeline_dir, "configurations.json"))
        labeling_budget = cfg.get("labeling_budget", "")
        selected_dataset = cfg.get("selected_dataset", "")
        results_list = cfg.get("results", [])
        for res in results_list:
            metrics = res.get("metrics", {})
            row = {
                "Time": res.get("Time", ""),
                "Pipeline Name": pipeline,
                "Dataset": selected_dataset,
                "Labeling Budget": labeling_budget,
                "Recall": metrics.get("Recall", ""),
                "F1": metrics.get("F1", ""),
                "Precision": metrics.get("Precision", "")
            }
            all_rows.append(row)

found_current_all = any(
    row["Pipeline Name"] == current_pipeline_name and row["Time"] == current_time
    for row in all_rows
)
if not found_current_all:
    current_cfg_all = load_config(os.path.join(current_pipeline_path, "configurations.json"))
    current_labeling_budget_all = current_cfg_all.get("labeling_budget", "")
    current_row_all = {
        "Time": current_time,
        "Pipeline Name": current_pipeline_name,
        "Dataset": current_dataset,
        "Labeling Budget": current_labeling_budget_all,
        "Recall": recall_score,
        "F1": f1_score,
        "Precision": precision_score
    }
    all_rows = [
        r for r in all_rows
        if not (r["Pipeline Name"] == current_pipeline_name and r["Time"].split(" ")[0] == current_time.split(" ")[0])
    ]
    all_rows.append(current_row_all)

all_df = pd.DataFrame(all_rows)
for col in ["Recall", "F1", "Precision", "Labeling Budget"]:
    if col in all_df.columns:
        all_df[col] = pd.to_numeric(all_df[col], errors="coerce").round(2)
all_df = all_df.sort_values(by="Time", ascending=False)

styled_all_df = all_df.style.apply(highlight_current, axis=1).format({
    "Recall": "{:.2f}",
    "F1": "{:.2f}",
    "Precision": "{:.2f}",
    "Labeling Budget": "{:}"
})

st.markdown("---")
st.markdown("#### Result Comparison (All Pipelines/Datasets):")
st.write("_(Click on column headers to sort the table.)_")
st.dataframe(styled_all_df)


st.markdown("---")
# Share Result button with additional share options
if st.button("Share Result"):
    share_text = (
        f"Check out my Matelda results! Recall: {recall_score:.2f}, "
        f"F1: {f1_score:.2f}, Precision: {precision_score:.2f}"
    )
    st.code(share_text)

st.balloons()
