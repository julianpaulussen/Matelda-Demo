import streamlit as st

st.title("Configurations")
st.subheader("Select a table")

# Table selection 
options = ["Quintet", "DGov_NT", "WDC"]
selected_table = st.radio(
    "Table Selection", 
    options, 
    index=options.index("Quintet"), 
    key="table_radio", 
    label_visibility="hidden"
)
st.write("Information about:", selected_table)
st.write("Here is some information about the selected table.")

st.markdown("---")
st.subheader("Select Labeling Budget")

# Initialize the session state for labeling_budget if it doesn't exist.
if "labeling_budget" not in st.session_state:
    st.session_state.labeling_budget = 10

# Use the saved value (or default) for the slider.
labeling_budget = st.slider(
    "Select Labeling Budget",
    min_value=1,
    max_value=100,
    value=st.session_state.labeling_budget,  # Use session state value here.
    key="budget_slider",
    label_visibility="hidden"
)

st.number_input(
    "Enter Labeling Budget",
    min_value=1,
    max_value=100,
    value=labeling_budget,
    step=1,
    key="budget_input",
    label_visibility="hidden"
)

st.markdown("---")

# Save configurations button.
if st.button("Save Configurations"):
    st.session_state.config_saved = True
    st.session_state.labeling_budget = st.session_state.budget_slider
    st.success("Configurations saved!")
    st.write("Saved budget:", st.session_state.labeling_budget)

if st.button("Next"):
    st.switch_page("pages/DomainBasedFolding.py")