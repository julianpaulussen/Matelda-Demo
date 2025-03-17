import streamlit as st

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

# Page Config (Optional)
st.set_page_config(page_title="Scrollable Page with Fixed Bottom Div", layout="wide")

# Custom CSS to make a floating div at the bottom
st.markdown("""
    <style>
        /* Make the main container scrollable */
        .main {
            height: 80vh;
            overflow-y: auto;
        }

        /* Fixed div at the bottom */
        .fixed-bottom {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: rgba(0, 0, 0, 0.8); /* Dark background */
            color: white;
            text-align: center;
            padding: 15px;
            font-size: 18px;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

# Create a scrollable container with a lot of content
st.title("Scrollable Page with Floating Bottom Div")

st.write("Scroll down to see the floating bottom section!")

for i in range(50):  # Adding multiple elements to create a scroll effect
    st.write(f"📜 This is line number {i+1}")

# Injecting the floating div at the bottom
st.markdown("""
    <div class="fixed-bottom">
        🚀 This is a fixed floating div at the bottom!
    </div>
""", unsafe_allow_html=True)
