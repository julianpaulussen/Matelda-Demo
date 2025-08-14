import os
import json
import streamlit as st
from components import render_sidebar, apply_base_styles

st.set_page_config(page_title="Labeling Mode", layout="wide")
st.title("Choose Labeling Mode")

apply_base_styles()
render_sidebar()

# Ensure dataset is configured
if "dataset_select" not in st.session_state and "pipeline_path" in st.session_state:
    cfg_path = os.path.join(st.session_state.pipeline_path, "configurations.json")
    if os.path.exists(cfg_path):
        with open(cfg_path) as f:
            cfg = json.load(f)
        sd = cfg.get("selected_dataset")
        if sd:
            st.session_state.dataset_select = sd

if "dataset_select" not in st.session_state:
    st.warning("Dataset not configured. Go back to Configurations.")
    if st.button("Go to Configurations"):
        st.switch_page("pages/Configurations.py")
    st.stop()

col1, col2 = st.columns(2)
with col1:
    st.subheader("Single Player")
    st.write("Label on your own, as before.")
    if st.button("Continue Single Player", use_container_width=True):
        st.switch_page("pages/Labeling.py")

with col2:
    st.subheader("Multiplayer")
    st.write("Host or join a live labeling session.")
    if st.button("Go Multiplayer", use_container_width=True):
        st.switch_page("pages/Multiplayer.py")

