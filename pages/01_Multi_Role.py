import streamlit as st
from components import render_sidebar, apply_base_styles, get_current_theme

st.set_page_config(page_title="Multiplayer: Role", layout="wide")
apply_base_styles(get_current_theme())

render_sidebar()

st.title("Multiplayer")
st.subheader("Choose role")

col1, col2 = st.columns(2)
with col1:
    if st.button("Host a session", use_container_width=True):
        st.switch_page("pages/02_Multi_Host.py")
with col2:
    if st.button("Join a session", use_container_width=True):
        st.switch_page("pages/03_Multi_Join.py")

