import os
import streamlit as st
from components import render_sidebar, apply_base_styles, get_current_theme

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

