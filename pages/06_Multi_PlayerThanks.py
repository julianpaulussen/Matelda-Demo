import streamlit as st
from components import render_sidebar, apply_base_styles, get_current_theme

st.set_page_config(page_title="Thank You", layout="wide")
apply_base_styles(get_current_theme())
render_sidebar()

st.title("Thank You")
st.write("Thanks for labeling, you can now close this page.")

