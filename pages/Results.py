import streamlit as st
import random

# Hide default Streamlit menu
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.page_link("app.py", label="Matelda")
    st.page_link("pages/Configurations.py", label="Configurations")
    st.page_link("pages/DomainBasedFolding.py", label="Domain Based Folding")
    st.page_link("pages/QualityBasedFolding.py", label="Quality Based Folding")
    st.page_link("pages/Labeling.py", label="Labeling")
    st.page_link("pages/ErrorDetection.py", label="Error Detection")
    st.page_link("pages/Results.py", label="Results")

st.title("Results")
st.write("### Model Performance Metrics")

# Generate random scores
recall_score = round(random.uniform(0.7, 0.95), 2)
f1_score = round(random.uniform(0.65, 0.92), 2)
precision_score = round(random.uniform(0.75, 0.96), 2)

# Display metrics in columns
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="Recall", value=f"{recall_score}")

with col2:
    st.metric(label="F1 Score", value=f"{f1_score}")

with col3:
    st.metric(label="Precision", value=f"{precision_score}")

st.balloons()
