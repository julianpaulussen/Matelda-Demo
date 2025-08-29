import requests
import streamlit as st
from components import render_sidebar, apply_base_styles, get_current_theme, render_inline_restart_button
from components.session_persistence import persist_session
from backend.api import ensure_api_started

st.set_page_config(page_title="Join Session", layout="wide")
apply_base_styles(get_current_theme())
render_sidebar()


API_BASE = ensure_api_started()


st.title("Join a Session")
st.caption("Enter a session code or use a URL containing ?session_id=...")

_ = API_BASE  # ensure started

try:
    qp = st.query_params
    sid_param = qp.get("session_id") if qp else None
except Exception:
    sid_param = None

sid = st.text_input("Session code", value=sid_param or "").strip()

# Auto-join if session_id present in URL and not already joined
if sid_param and not st.session_state.get("mp.session_id"):
    try:
        meta = requests.get(f"{API_BASE}/sessions/{sid_param}", timeout=5)
        if meta.status_code == 200:
            p = requests.post(f"{API_BASE}/sessions/{sid_param}/players", json={"role": "player"}, timeout=5).json()
            st.session_state["mp.session_id"] = sid_param
            st.session_state["mp.player_id"] = p["player_id"]
            st.session_state["mp.display_name"] = p["display_name"]
            st.session_state["mp.role"] = "player"
            persist_session()
            st.switch_page("pages/04_Multi_PlayerLobby.py")
            st.stop()
    except Exception:
        # Fall through to manual join UI on any error
        pass

if st.button("Join") and sid:
    try:
        meta = requests.get(f"{API_BASE}/sessions/{sid}", timeout=5)
        if meta.status_code != 200:
            st.error("Session not found")
        else:
            p = requests.post(f"{API_BASE}/sessions/{sid}/players", json={"role": "player"}, timeout=5).json()
            st.session_state["mp.session_id"] = sid
            st.session_state["mp.player_id"] = p["player_id"]
            st.session_state["mp.display_name"] = p["display_name"]
            st.session_state["mp.role"] = "player"
            # Persist immediately to survive reloads
            persist_session()
            st.switch_page("pages/04_Multi_PlayerLobby.py")
    except Exception as e:
        st.error(f"Failed to join: {e}")

st.markdown("---")
nav_cols = st.columns([1, 1, 1], gap="small")

with nav_cols[0]:
    render_inline_restart_button(page_id="join", use_container_width=True)

with nav_cols[1]:
    if st.button("Back", key="join_back", use_container_width=True):
        st.switch_page("pages/01_Multi_Role.py")

with nav_cols[2]:
    if st.button("Next", key="join_next", use_container_width=True):
        # Attempt to join using the entered sid
        if sid:
            try:
                meta = requests.get(f"{API_BASE}/sessions/{sid}", timeout=5)
                if meta.status_code != 200:
                    st.error("Session not found")
                else:
                    p = requests.post(f"{API_BASE}/sessions/{sid}/players", json={"role": "player"}, timeout=5).json()
                    st.session_state["mp.session_id"] = sid
                    st.session_state["mp.player_id"] = p["player_id"]
                    st.session_state["mp.display_name"] = p["display_name"]
                    st.session_state["mp.role"] = "player"
                    from components.session_persistence import persist_session
                    persist_session()
                    st.switch_page("pages/04_Multi_PlayerLobby.py")
            except Exception as e:
                st.error(f"Failed to join: {e}")
