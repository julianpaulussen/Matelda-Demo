import requests
import streamlit as st
from components import render_sidebar, apply_base_styles, get_current_theme, get_base_url, render_inline_restart_button
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
    # Join URL (no copy button)
    st.caption("Join URL")
    st.code(join_url)

    # Session code (no copy button)
    st.caption("Session Code")
    st.code(sid)
    # QR (show precise error only if import fails)
    try:
        import qrcode  # type: ignore
        from io import BytesIO
        img = qrcode.make(join_url)
        # Convert to PNG bytes to avoid backend/image type mismatches
        pil_img = img.get_image() if hasattr(img, "get_image") else img
        buf = BytesIO()
        pil_img.save(buf, format="PNG")
        st.image(buf.getvalue(), caption="Scan to join")
    except ImportError:
        st.warning("QR support not available. Install with: pip install 'qrcode[pil]'")
    except Exception as e:
        st.error(f"Failed generating QR: {e}")

# Players block
with st.container(border=True):
    st.subheader("Players")
    if st.button("Refresh now"):
        st.rerun()
    st.info("Once all players are in, click Refresh now to update their status before starting.")
    try:
        meta = requests.get(f"{API_BASE}/sessions/{sid}", timeout=10).json()
        for p in meta.get("players", []):
            st.write(f"- {p.get('display_name')} ({p.get('role')}) — {p.get('status')}")
    except Exception as e:
        st.error(f"Failed to fetch players: {e}")

st.markdown("---")
nav_cols = st.columns([1, 1, 1], gap="small")

with nav_cols[0]:
    render_inline_restart_button(page_id="host", use_container_width=True)

with nav_cols[1]:
    if st.button("Back", use_container_width=True):
        st.switch_page("pages/01_Multi_Role.py")

with nav_cols[2]:
    if st.button("Start Session", type="primary", use_container_width=True):
        @st.dialog("Start Session Now?", width="medium")
        def _confirm_start_dialog():
            st.write("Are you sure all players have joined? Starting will assign items to players.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🆗 Yes, start", key="host_start_confirm", use_container_width=True):
                    try:
                        requests.post(f"{API_BASE}/sessions/{sid}/start", timeout=10)
                        st.switch_page("pages/05_Multi_PlayerLabel.py")
                    except Exception as e:
                        st.error(f"Failed to start: {e}")
            with col2:
                if st.button("Cancel", key="host_start_cancel", use_container_width=True):
                    st.rerun()
        _confirm_start_dialog()
