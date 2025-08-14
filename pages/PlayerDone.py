import streamlit as st
from components import render_sidebar, apply_base_styles

st.set_page_config(page_title="Thank You", layout="wide")
st.title("Thanks for labeling!")
apply_base_styles()
render_sidebar()

st.success("You’re all set. You can now close this page.")

