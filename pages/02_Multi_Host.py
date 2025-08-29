import os
import json
import requests
import streamlit as st
from components import render_sidebar, apply_base_styles, get_current_theme
from components.session_persistence import persist_session
from backend.backend import backend_sample_labeling

st.set_page_config(page_title="Host Lobby", layout="wide")
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


st.title("Host Lobby")
st.caption("Create a multiplayer session and wait for players to join.")

if "mp.session_id" not in st.session_state:
    st.session_state["mp.session_id"] = None
    st.session_state["mp.player_id"] = None
    st.session_state["mp.display_name"] = None
    st.session_state["mp.role"] = "host"

if not ensure_api():
    st.stop()

# Auto-create session on first load
if not st.session_state.get("mp.session_id"):
    try:
        min_budget = int(st.session_state.get("labeling_budget", 10))
        resp = requests.post(
            f"{api_base()}/api/sessions", json={"min_budget": int(min_budget)}, timeout=5
        )
        resp.raise_for_status()
        data = resp.json()
        st.session_state["mp.session_id"] = data["session_id"]
        # Register host as a player
        p = requests.post(
            f"{api_base()}/api/sessions/{data['session_id']}/players",
            json={"role": "host"},
            timeout=5,
        ).json()
        st.session_state["mp.player_id"] = p["player_id"]
        st.session_state["mp.display_name"] = p["display_name"]
        persist_session()
    except Exception as e:
        st.error(f"Failed to create session: {e}")
        st.stop()

sid = st.session_state.get("mp.session_id")
if not sid:
    st.stop()

st.markdown("---")

with st.container(border=True):
    st.subheader("Invite Players")
    base_url = os.environ.get("BASE_URL", "http://localhost:8501")
    join_url = f"{base_url}/?session_id={sid}"

    st.code(join_url)
    st.caption("Use the copy button to share.")

    try:
        import qrcode  # type: ignore
    except ImportError:
        st.warning("QR support missing. Install with: pip install 'qrcode[pil]'")
        st.info("Use the Join URL above.")
    else:
        try:
            from io import BytesIO
            qr = qrcode.QRCode(version=1, box_size=6, border=2)
            qr.add_data(join_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buf = BytesIO()
            img.save(buf, format="PNG")
            st.image(buf.getvalue(), caption="Scan to join")
        except Exception as e:
            st.error(f"Failed to render QR: {e}")
            st.info("Use the Join URL above.")

with st.container(border=True):
    st.subheader("Players")
    live = st.checkbox("Live updates (auto-refresh)", key="host_live", value=False)
    if st.button("Refresh now"):
        st.rerun()
    if live:
        import time
        time.sleep(3.5)
        st.rerun()

    try:
        meta = requests.get(f"{api_base()}/api/sessions/{sid}", timeout=5).json()
        players = meta.get("players", [])
        for p in players:
            st.write(f"- {p['display_name']} ({p['role']}) — {p['status']}")
    except Exception as e:
        st.error(f"Failed to fetch players: {e}")

st.markdown("---")

colA, colB = st.columns(2)
with colA:
    if st.button("Start session", type="primary"):
        try:
            # Compute total budget = labeling_budget x players
            dataset = st.session_state.get("dataset_select")
            cell_folds = st.session_state.get("cell_folds", {})
            domain_folds = st.session_state.get("domain_folds", {})
            meta = requests.get(f"{api_base()}/api/sessions/{sid}", timeout=5).json()
            players = meta.get("players", [])
            per_player = int(st.session_state.get("labeling_budget", 10))
            total_budget = per_player * max(1, len(players))

            # Only host computes the pool and saves it server-side
            pool = backend_sample_labeling(dataset, total_budget, cell_folds, domain_folds)
            samples = [
                {
                    "sample_id": str(c.get("id")),
                    "dataset": dataset,
                    "table": c.get("table"),
                    "row": int(c.get("row", 0)),
                    "col": c.get("col"),
                    "val": c.get("val"),
                }
                for c in pool
            ]
            requests.post(f"{api_base()}/api/sessions/{sid}/pool", json=samples, timeout=15)

            # Start session: server reserves first M for first player, etc.
            requests.post(f"{api_base()}/api/sessions/{sid}/start", timeout=5)
            # Host labels as a player too (multiplayer page)
            st.switch_page("pages/05_Multi_PlayerLabel.py")
        except Exception as e:
            st.error(f"Failed to start: {e}")
with colB:
    if st.button("Back"):
        st.switch_page("pages/01_Multi_Role.py")
