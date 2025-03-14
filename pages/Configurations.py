import streamlit as st

params = st.query_params
current_page = params.get("page", "Configurations")

if current_page != "Configurations":
    params["page"] = "Configurations"
    st.stop()

    

st.title("Configurations")
st.subheader("Select a table")

# Table selection with a default.
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

# Labeling budget widgets (default value is 10)
st.markdown("---")
st.subheader("Select Labeling Budget")
labeling_budget = st.slider("",1, 1000, 10, key="budget_slider")
st.number_input("Enter Labeling Budget (Integers Only)", 1, 1000, labeling_budget, key="budget_input", step=1)
st.write(f"Labeling Budget is set to: {labeling_budget}")

st.markdown("---")

# Save configurations button.
if st.button("Save Configurations"):
    st.success("Configurations saved!")
    st.session_state.config_saved = True

# ToDo: Insert Next button 
# Show Next button only if configurations have been saved.
#if st.session_state.get("config_saved"):
#    if st.button("Next"):
#        st.query_params["page"] = "DomainBasedFolding"
#        st.stop()
