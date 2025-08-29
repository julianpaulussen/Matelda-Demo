import os
import streamlit as st
from components import render_sidebar, apply_base_styles, get_current_theme, render_inline_restart_button

st.set_page_config(page_title="Mode Select", layout="wide")
apply_base_styles(get_current_theme())

st.title("Mode Select")
st.write("Choose how you want to label:")

# Sidebar
render_sidebar()

col1, col2 = st.columns(2)
with col1:
    if st.button("Single Player", use_container_width=True):
        st.switch_page("pages/Labeling.py")

with col2:
    if st.button("Multiplayer", use_container_width=True):
        st.switch_page("pages/01_Multi_Role.py")

st.markdown("---")
nav_cols = st.columns([1, 1, 1], gap="small")

with nav_cols[0]:
    render_inline_restart_button(page_id="mode_select", use_container_width=True)

with nav_cols[1]:
    if st.button("Back", key="mode_back", use_container_width=True):
        st.switch_page("pages/Configurations.py")

with nav_cols[2]:
    if st.button("Next", key="mode_next", use_container_width=True):
        st.switch_page("pages/Labeling.py")
