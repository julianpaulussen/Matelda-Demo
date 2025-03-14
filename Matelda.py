import streamlit as st

# Get the current query parameters.
params = st.query_params
current_page = params.get("page", "Matelda")

if current_page != "Matelda":
    # Update the query parameter by assigning directly.
    params["page"] = "Matelda"
    st.stop()

st.title("Matelda")
st.write("Welcome to Matelda! Click the button below to continue to Configurations.")

# ToDo: Insert Next button 
#if st.button("Next"):
#    # Set the new query parameter value.
#    st.query_params["page"] = "Configurations"
#    st.stop()
