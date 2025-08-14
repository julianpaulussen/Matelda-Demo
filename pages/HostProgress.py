import os
import json
import time
import streamlit as st
from typing import List, Dict, Any

from components import render_sidebar, apply_base_styles
from backend.multiplayer import get_session, all_players_done, run_propagation_for_session

st.set_page_config(page_title="Host Progress", layout="wide")
st.title("Players' Progress")
apply_base_styles()
render_sidebar()

query = st.query_params
session_id = query.get("session") if isinstance(query.get("session"), str) else (query.get("session")[0] if query.get("session") else None)
pipeline_path = st.session_state.get("pipeline_path")

if not (session_id and pipeline_path):
    st.error("Missing session data or pipeline.")
    st.stop()

sess = get_session(pipeline_path, session_id)
if not sess:
    st.error("Session not found.")
    st.stop()

st.subheader(f"Session {session_id}")
players: List[Dict[str, Any]] = list(sess.get("players", {}).values())
for p in players:
    status = p.get("status", "joined")
    name = p.get("name", "Player") + (" (Host)" if p.get("is_host") else "")
    emoji = "✅" if status == "done" else ("✍️" if status == "labeling" else "🟡")
    st.write(f"- {emoji} {name}: {status}")

st.markdown("---")
cols = st.columns([1, 1])
if cols[0].button("Refresh"):
    st.rerun()

proceed_label = "Proceed (even if not all done)"
if cols[1].button(proceed_label, type="primary"):
    # Aggregate and run propagation for the host's flow
    propagation_results = run_propagation_for_session(pipeline_path, session_id)
    st.session_state.propagation_results = propagation_results
    st.session_state.propagation_saved = False
    st.switch_page("pages/PropagatedErrors.py")

# Auto-refresh to show changes quickly
st.checkbox(
    "Auto-refresh",
    value=st.session_state.get("mp_auto_refresh", False),
    key="mp_auto_refresh",
)
if st.session_state.get("mp_auto_refresh", False):
    time.sleep(2.0)
    st.rerun()
