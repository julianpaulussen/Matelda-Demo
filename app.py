import streamlit as st
from components import render_sidebar, apply_base_styles

st.set_page_config(page_title="Matelda", layout="wide")

# Apply base styles
apply_base_styles()

st.title("Matelda")
st.write("Welcome to Matelda!")
st.markdown("""Read the full paper [here](https://www.openproceedings.org/2025/conf/edbt/paper-98.pdf) or click the button below to continue with configurations.""")

# Sidebar Navigation
render_sidebar()

# Start Button
if st.button("Start"):
    st.switch_page("pages/Configurations.py")
