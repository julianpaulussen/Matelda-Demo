import os
import json
import time
from io import BytesIO
from typing import Optional

import streamlit as st

from components import render_sidebar, apply_base_styles
from backend.multiplayer import (
    create_session,
    get_session,
    join_session,
    list_players,
    start_session,
)

st.set_page_config(page_title="Multiplayer", layout="wide")
st.title("Multiplayer Labeling")
apply_base_styles()
render_sidebar()


def _load_cfg_dataset() -> Optional[str]:
    if "dataset_select" not in st.session_state and "pipeline_path" in st.session_state:
        p = os.path.join(st.session_state.pipeline_path, "configurations.json")
        if os.path.exists(p):
            with open(p) as f:
                cfg = json.load(f)
            sel = cfg.get("selected_dataset")
            if sel:
                st.session_state.dataset_select = sel
    return st.session_state.get("dataset_select")


dataset = _load_cfg_dataset()
if not dataset:
    st.warning("Dataset not configured. Go back to Configurations.")
    if st.button("Go to Configurations"):
        st.switch_page("pages/Configurations.py")
    st.stop()


def _pipeline_cfg():
    p = st.session_state.get("pipeline_path")
    if not p:
        return None
    cfg_path = os.path.join(p, "configurations.json")
    if not os.path.exists(cfg_path):
        return None
    with open(cfg_path) as f:
        return json.load(f)


cfg = _pipeline_cfg()
if not cfg:
    st.warning("No pipeline selected.")
    st.stop()

labeling_budget = cfg.get("labeling_budget", 10)
cell_folds = cfg.get("cell_folds", {})
domain_folds = cfg.get("domain_folds", {})


def _base_url() -> str:
    # Best effort: allow override; otherwise default to localhost
    return os.environ.get("BASE_URL", "http://192.168.178.45:8501")


def _autorefresh(seconds: float = 2.0):
    # Only refresh if user explicitly enabled it
    if st.session_state.get("mp_auto_refresh", False):
        time.sleep(seconds)
        st.rerun()


query = st.query_params
pipeline_path = st.session_state.pipeline_path


def render_host_lobby(session_id: str, host_id: str):
    st.subheader("Host Session")
    join_link = f"{_base_url()}/?page=Multiplayer&join={session_id}"
    st.write("Share this link or QR code:")
    st.code(join_link, language="text")
    try:
        import qrcode
        img = qrcode.make(join_link)
        st.image(img, caption="Scan to join")
    except ImportError:
        st.info("Install the 'qrcode' package to display a QR code.")
    except Exception as e:
        st.warning(f"Could not render QR code: {e}")

    st.markdown("---")
    st.write("Players in session:")
    plist = list_players(pipeline_path, session_id)
    for p in plist:
        status = p.get("status", "joined")
        st.write(f"- {p.get('name', 'Player')} ({status})")

    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("Start Session", type="primary", use_container_width=True):
            start_session(pipeline_path, session_id)
            # Redirect host to labeling page with query params
            st.query_params["session"] = session_id
            st.query_params["player"] = host_id
            st.switch_page("pages/MultiplayerLabeling.py")
    with c2:
        st.checkbox(
            "Auto-refresh",
            value=st.session_state.get("mp_auto_refresh", False),
            key="mp_auto_refresh",
            help="Enable to auto-update player list",
        )
    _autorefresh(2.0)


def render_join_waiting(session_id: str, player_id: str):
    st.subheader("Waiting for host to start…")
    sess = get_session(pipeline_path, session_id)
    st.write(f"Session: {session_id}")
    st.write("Players:")
    for p in list_players(pipeline_path, session_id):
        st.write(f"- {p.get('name', 'Player')} ({p.get('status', 'joined')})")
    # If running, go to labeling
    if sess.get("status") == "running":
        st.query_params["session"] = session_id
        st.query_params["player"] = player_id
        st.switch_page("pages/MultiplayerLabeling.py")
    st.checkbox(
        "Auto-refresh",
        value=st.session_state.get("mp_auto_refresh", False),
        key="mp_auto_refresh",
        help="Enable to auto-update status",
    )
    _autorefresh(2.0)


# Fast-path: joined via QR code
if "join" in query:
    code = query.get("join")
    if isinstance(code, list):
        code = code[0]
    pid = st.session_state.get("mp_player_id")
    sid = st.session_state.get("mp_session_id")
    if not (sid and pid) or sid != code:
        player_id, name = join_session(pipeline_path, code)
        if not player_id:
            st.error("Invalid or closed session code.")
            st.stop()
        st.session_state.mp_session_id = code
        st.session_state.mp_player_id = player_id
        st.session_state.mp_player_name = name
    render_join_waiting(st.session_state.mp_session_id, st.session_state.mp_player_id)
    st.stop()


mode = st.radio("Mode", ["Host", "Join"], horizontal=True)

if mode == "Host":
    # Back button on initial host page
    back_cols = st.columns([1, 3])
    if back_cols[0].button("Back", use_container_width=True):
        st.switch_page("pages/LabelingMode.py")

    if st.button("Create Session", type="primary"):
        session_id, host_id = create_session(
            pipeline_path,
            dataset,
            labeling_budget,
            cell_folds,
            domain_folds,
        )
        st.session_state.mp_session_id = session_id
        st.session_state.mp_player_id = host_id
        # Name is assigned in backend; keep for convenience if needed
        st.session_state.mp_player_name = st.session_state.get("mp_player_name", "Host")
        st.rerun()
    if st.session_state.get("mp_session_id") and st.session_state.get("mp_player_id"):
        render_host_lobby(st.session_state.mp_session_id, st.session_state.mp_player_id)
    else:
        st.info("Click 'Create Session' to start hosting.")
else:
    st.write("Enter session code from the host, or use the QR link.")
    code = st.text_input("Session code", value="")
    if st.button("Join Session", use_container_width=False) and code:
        player_id, name = join_session(pipeline_path, code)
        if not player_id:
            st.error("Invalid or closed session code.")
        else:
            st.session_state.mp_session_id = code
            st.session_state.mp_player_id = player_id
            st.session_state.mp_player_name = name
            st.rerun()
    if st.session_state.get("mp_session_id") and st.session_state.get("mp_player_id"):
        render_join_waiting(st.session_state.mp_session_id, st.session_state.mp_player_id)
