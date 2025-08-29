import requests
import streamlit as st
from components import render_sidebar, apply_base_styles, get_current_theme, get_base_url
from backend.api import ensure_api_started

st.set_page_config(page_title="Host Lobby", layout="wide")
apply_base_styles(get_current_theme())
render_sidebar()

API_BASE = ensure_api_started()

st.title("Host Lobby")
st.caption("Create a multiplayer session and invite players.")

# Auto-create session and host player once
if not st.session_state.get("mp.session_id"):
    try:
        # Resolve labeling budget from session or pipeline config
        min_budget = None
        # Prefer explicit labeling_budget
        if st.session_state.get("labeling_budget") is not None:
            min_budget = int(st.session_state.get("labeling_budget"))
        # Fallback to UI input fields if used earlier
        elif st.session_state.get("budget_input") is not None:
            min_budget = int(st.session_state.get("budget_input"))
        # Final fallback: read from configurations.json
        if min_budget is None and st.session_state.get("pipeline_path"):
            import os, json
            cfg_path = os.path.join(st.session_state.pipeline_path, "configurations.json")
            if os.path.exists(cfg_path):
                try:
                    with open(cfg_path) as f:
                        cfg = json.load(f)
                    if cfg.get("labeling_budget") is not None:
                        min_budget = int(cfg.get("labeling_budget", 10))
                except Exception:
                    pass
        if min_budget is None:
            min_budget = 10
        r = requests.post(f"{API_BASE}/sessions", json={"min_budget": min_budget}, timeout=10)
        r.raise_for_status()
        data = r.json()
        sid = data["session_id"]
        st.session_state["mp.session_id"] = sid
        st.session_state["mp.role"] = "host"
        # Create host player
        p = requests.post(f"{API_BASE}/sessions/{sid}/players", json={"role": "host"}, timeout=10).json()
        st.session_state["mp.player_id"] = p["player_id"]
        st.session_state["mp.display_name"] = p["display_name"]
    except Exception as e:
        st.error(f"Failed to create session: {e}")
        st.stop()

sid = st.session_state.get("mp.session_id")
pid = st.session_state.get("mp.player_id")
name = st.session_state.get("mp.display_name")

st.markdown("---")

# Invite block
with st.container(border=True):
    st.subheader("Invite Players")
    origin = get_base_url()
    join_url = f"{origin}/?session_id={sid}"
    st.text_input("Join URL", value=join_url, key="mp.join_url_display", disabled=True, label_visibility="collapsed")
    if st.button("Copy link", use_container_width=True):
        try:
            from streamlit_javascript import st_javascript  # type: ignore
            st_javascript(f'navigator.clipboard.writeText("{join_url}")')
            st.success("Copied to clipboard")
        except Exception:
            st.info("Copy not available; select and copy the field above.")
    # QR
    try:
        import qrcode
        img = qrcode.make(join_url)
        st.image(img, caption="Scan to join")
    except Exception:
        st.warning("Install QR support: pip install 'qrcode[pil]'")

# Players block
with st.container(border=True):
    st.subheader("Players")
    auto = st.checkbox("Live updates (auto-refresh)", value=False)
    if st.button("Refresh now"):
        st.rerun()
    if auto:
        try:
            from streamlit_autorefresh import st_autorefresh
            st_autorefresh(interval=3500, key="host_lobby_refresh")
        except Exception:
            pass
    try:
        meta = requests.get(f"{API_BASE}/sessions/{sid}", timeout=10).json()
        for p in meta.get("players", []):
            st.write(f"- {p.get('display_name')} ({p.get('role')}) — {p.get('status')}")
    except Exception as e:
        st.error(f"Failed to fetch players: {e}")

st.markdown("---")
colA, colB = st.columns(2)
with colA:
    if st.button("Start session", type="primary", use_container_width=True):
        try:
            # Trigger background preparation; then host proceeds to player labeling view
            requests.post(f"{API_BASE}/sessions/{sid}/start", timeout=10)
            st.switch_page("pages/05_Multi_PlayerLabel.py")
        except Exception as e:
            st.error(f"Failed to start: {e}")
with colB:
    if st.button("Back", use_container_width=True):
        st.switch_page("pages/01_Multi_Role.py")
