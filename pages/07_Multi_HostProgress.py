import requests
import streamlit as st
from components import render_sidebar, apply_base_styles, get_current_theme, render_inline_restart_button
from backend.api import ensure_api_started

st.set_page_config(page_title="Host Progress", layout="wide")
apply_base_styles(get_current_theme())
render_sidebar()


API_BASE = ensure_api_started()


st.title("Session Progress")

sid = st.session_state.get("mp.session_id")
if not sid:
    st.warning("No session active.")
    st.stop()

live = st.checkbox("Live updates (auto-refresh)", key="host_progress_live", value=False)
if st.button("Refresh now"):
    st.rerun()
if live:
    import time
    time.sleep(3.5)
    st.rerun()

all_done = False
try:
    prog = requests.get(f"{API_BASE}/sessions/{sid}/progress", timeout=10).json()
    players = prog.get("players", [])
    all_done = bool(prog.get("all_done", False))
    for p in players:
        status_text = "Done" if p["status"] == "done" else "Still labeling"
        st.write(f"- {p['display_name']} — {status_text}")
    if all_done:
        st.success("All players are done. You can continue to Propagated Errors.")
    else:
        st.warning("Some players are still labeling. You can wait or continue without them.")
    # Clear confirmation flag if everyone is done now
    if all_done and st.session_state.get("host_progress_confirm_continue"):
        st.session_state.host_progress_confirm_continue = False
except Exception as e:
    st.error(f"Failed to fetch progress: {e}")

st.markdown("---")

nav_cols = st.columns([1, 1, 1], gap="small")

with nav_cols[0]:
    render_inline_restart_button(page_id="host_progress", use_container_width=True)

with nav_cols[1]:
    if st.button("Back to Labeling", use_container_width=True):
        st.switch_page("pages/05_Multi_PlayerLabel.py")

with nav_cols[2]:
    if st.button("Next", type="primary", use_container_width=True):
        if not all_done:
            @st.dialog("Continue Without All Players?", width="medium")
            def _confirm_continue_dialog():
                st.write("Some players are still labeling. Do you want to continue without waiting for their labels?")
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("⏩ Continue Anyway", key="confirm_continue_anyway", use_container_width=True):
                        st.switch_page("pages/PropagatedErrors.py")
                with col_b:
                    if st.button("🔄 Refresh / Wait", key="confirm_refresh_wait", use_container_width=True):
                        st.rerun()
                if st.button("Cancel", key="confirm_continue_cancel"):
                    st.rerun()
            _confirm_continue_dialog()
        else:
            # Everyone done: signal backend to export then proceed
            try:
                requests.post(f"{API_BASE}/sessions/{sid}/next", timeout=10)
            except Exception:
                pass
            st.switch_page("pages/PropagatedErrors.py")
