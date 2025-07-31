"""
Common sidebar navigation component for all pages
"""
import streamlit as st


def render_sidebar():
    """Render the common sidebar navigation"""
    with st.sidebar:
        st.page_link("app.py", label="Matelda")
        st.page_link("pages/Configurations.py", label="Configurations")
        st.page_link("pages/DomainBasedFolding.py", label="Domain Based Folding")
        st.page_link("pages/QualityBasedFolding.py", label="Quality Based Folding")
        st.page_link("pages/Labeling.py", label="Labeling")
        st.page_link("pages/PropagatedErrors.py", label="Propagated Errors")
        st.page_link("pages/ErrorDetection.py", label="Error Detection")
        st.page_link("pages/Results.py", label="Results")
