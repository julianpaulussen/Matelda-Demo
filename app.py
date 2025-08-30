import streamlit as st
from components import render_sidebar, apply_base_styles, get_current_theme
from backend.api import ensure_api_started
from components.session_persistence import clear_persisted_session

st.set_page_config(
    page_title="Matelda", 
    layout="wide",
    page_icon="🔧",
    initial_sidebar_state="expanded"
)

# Apply base styles with current theme
current_theme = get_current_theme()
apply_base_styles(current_theme)

# Ensure multiplayer backend is running whenever the app starts
try:
    _ = ensure_api_started()
except Exception:
    # Non-fatal if backend can't start; pages that need it will show errors
    pass

# If a join URL (?session_id=...) hits the root app, redirect to Join page
try:
    qp = st.query_params
    if qp and "session_id" in qp and qp.get("session_id"):
        st.switch_page("pages/03_Multi_Join.py")
except Exception:
    pass

st.title("Matelda")
st.write("Welcome to Matelda!")
st.markdown("""            
Real-world datasets are often fragmented across multiple heterogeneous tables, managed by different teams or organizations. Ensuring data quality in such environments is challenging, as traditional error detection tools typically operate on isolated tables and overlook cross-table relationships. To address this gap, we investigate how cleaning multiple tables simultaneously, combined with structured user collaboration, can reduce annotation effort and enhance the effectiveness and efficiency of error detection. 
            
We present Matelda, an interactive system for multi-table error detection that combines automated error detection with human-in-the-loop refinement. Matelda guides users through Inspection & Action, allowing them to explore system-generated insights, refine decisions, and annotate data with contextual support. It organizes tables using domain-based and quality-based folding and leverages semi-supervised learning to propagate labels across related tables efficiently. Our demonstration showcases Matelda’s capabilities for collaborative error detection and resolution by leveraging shared knowledge, contextual similarity, and structured user interactions across multiple tables. 
            
For more information on this project, please refer to our paper [Demonstrating Matelda for Multi-Table Error Detection](https://www.vldb.org/pvldb/vol18/p5379-ahmadi.pdf).
The Repository of the Demo is available on [GitHub](https://github.com/julianpaulussen/Matelda-Demo).

Click the button below to start the demo. If you have any questions, please feel free to ask us. 
            
Best,\\
Fatemeh Ahmadi, Julian Paulußen, Ziawasch Abedjan 
""")

# Sidebar Navigation
render_sidebar()

# Start Button
if st.button("Start"):
    # Check if there's an existing pipeline or session data
    has_existing_pipeline = (
        "pipeline_path" in st.session_state or 
        "dataset_select" in st.session_state or
        "selected_strategies" in st.session_state or
        any(key.startswith(("budget_", "labeling_", "domain_", "cell_")) for key in st.session_state.keys())
    )
    
    if has_existing_pipeline:
        @st.dialog("Start New Pipeline?", width="medium")
        def _confirm_start_dialog():
            st.write(
                "You already have a pipeline in progress. What would you like to do?"
            )
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("🔄 Continue Current Pipeline", key="continue_current", use_container_width=True):
                    st.switch_page("pages/Configurations.py")
                    
            with col_b:
                if st.button("🆕 Start Fresh Pipeline", key="start_fresh", use_container_width=True):
                    # Clear all session state to start from scratch (similar to restart functionality)
                    clear_persisted_session()
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.switch_page("pages/Configurations.py")
                    
            st.markdown("---")
            st.info("💾 Your existing pipeline is automatically saved and can be accessed via 'Use Existing Pipeline' in Configurations.")
            
            if st.button("Cancel", key="cancel_start"):
                st.rerun()  # Close dialog
                
        _confirm_start_dialog()
    else:
        # No existing pipeline, proceed normally
        st.switch_page("pages/Configurations.py")
