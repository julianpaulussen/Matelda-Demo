import os
import requests
import streamlit as st
from components import render_sidebar, apply_base_styles, get_current_theme
from components.session_persistence import persist_session

st.set_page_config(page_title="Join Session", layout="wide")
apply_base_styles(get_current_theme())
render_sidebar()


def api_base() -> str:
    return os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")


def ensure_api():
    try:
        r = requests.get(f"{api_base()}/health", timeout=2)
        if r.status_code == 200:
            return True
    except Exception:
        pass
    st.warning(
        "Backend API not reachable. Start it with: `uvicorn backend.api:app --reload` (default http://127.0.0.1:8000)."
    )
    return False


st.title("Join a Session")
st.caption("Enter a session code or use a URL containing ?session_id=...")

if not ensure_api():
    st.stop()

try:
    qp = st.query_params
    sid_param = qp.get("session_id") if qp else None
except Exception:
    sid_param = None

sid = st.text_input("Session code", value=sid_param or "").strip()

# Auto-join if session_id present in URL and not already joined
if sid_param and not st.session_state.get("mp.session_id"):
    try:
        meta = requests.get(f"{api_base()}/api/sessions/{sid_param}", timeout=5)
        if meta.status_code == 200:
            p = requests.post(
                f"{api_base()}/api/sessions/{sid_param}/players", json={"role": "player"}, timeout=5
            ).json()
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
        meta = requests.get(f"{api_base()}/api/sessions/{sid}", timeout=5)
        if meta.status_code != 200:
            st.error("Session not found")
        else:
            p = requests.post(
                f"{api_base()}/api/sessions/{sid}/players", json={"role": "player"}, timeout=5
            ).json()
            st.session_state["mp.session_id"] = sid
            st.session_state["mp.player_id"] = p["player_id"]
            st.session_state["mp.display_name"] = p["display_name"]
            st.session_state["mp.role"] = "player"
            # Persist immediately to survive reloads
            persist_session()
            st.switch_page("pages/04_Multi_PlayerLobby.py")
    except Exception as e:
        st.error(f"Failed to join: {e}")
