import requests
import streamlit as st
from components import render_sidebar, apply_base_styles, get_current_theme
from backend.api import ensure_api_started

st.set_page_config(page_title="Player Lobby", layout="wide")
apply_base_styles(get_current_theme())
render_sidebar()

API_BASE = ensure_api_started()


st.title("Lobby")

sid = st.session_state.get("mp.session_id")
pid = st.session_state.get("mp.player_id")
name = st.session_state.get("mp.display_name")

if not (sid and pid):
    st.warning("No session joined. Go to Join page.")
    st.stop()

st.info(f"You are: {name}")

if st.button("Refresh now"):
    st.rerun()
st.info("Waiting for host to start. Click Refresh to check the status.")

try:
    meta = requests.get(f"{API_BASE}/sessions/{sid}", timeout=5).json()
    status = meta.get("status")
    st.write(f"Session: {sid} — Status: {status}")
    st.subheader("Players")
    for p in meta.get("players", []):
        st.write(f"- {p['display_name']} ({p['status']})")
    if status == "active":
        st.switch_page("pages/05_Multi_PlayerLabel.py")
    else:
        st.caption("Waiting for host to start...")
except Exception as e:
    st.error(f"Failed to fetch session: {e}")
