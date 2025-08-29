import os
import requests
import streamlit as st
from components import render_sidebar, apply_base_styles, get_current_theme

st.set_page_config(page_title="Host Progress", layout="wide")
apply_base_styles(get_current_theme())
render_sidebar()


def api_base() -> str:
    return os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")


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

try:
    prog = requests.get(f"{api_base()}/api/sessions/{sid}/progress", timeout=5).json()
    players = prog.get("players", [])
    for p in players:
        status_text = "Done" if p["status"] == "done" else "Still labeling"
        st.write(f"- {p['display_name']} — {status_text}")
except Exception as e:
    st.error(f"Failed to fetch progress: {e}")

st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    if st.button("Next", type="primary"):
        try:
            # Fetch merged labels and pool, then hydrate local session for propagation
            merged = requests.get(f"{api_base()}/api/sessions/{sid}/labels", timeout=10).json().get("labels", [])
            pool = requests.get(f"{api_base()}/api/sessions/{sid}/pool", timeout=10).json().get("samples", [])

            # Prepare sampled_cells and labeling_results to match single-player expectations
            st.session_state.sampled_cells = [
                {
                    "id": s.get("sample_id"),
                    "name": f"{s.get('dataset','')} – {s.get('table','')}",
                    "table": s.get("table"),
                    "row": s.get("row"),
                    "col": s.get("col"),
                    "val": s.get("val"),
                    "domain_fold": "",
                    "cell_fold": "",
                    "cell_fold_label": "neutral",
                    "strategies": {},
                }
                for s in pool
            ]
            st.session_state.labeling_results = {}
            for m in merged:
                sid_ = str(m.get("sample_id"))
                lv = m.get("label_value")
                if lv is not None:
                    st.session_state.labeling_results[sid_] = (str(lv).lower() == "true")
            # Mark session next
            requests.post(f"{api_base()}/api/sessions/{sid}/next", timeout=5)
        except Exception:
            pass
        # Continue normal flow: go to Propagated Errors for propagation
        st.switch_page("pages/PropagatedErrors.py")
with col2:
    if st.button("Back to Labeling"):
        st.switch_page("pages/Labeling.py")
