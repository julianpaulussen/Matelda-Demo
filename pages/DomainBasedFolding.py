import streamlit as st

params = st.query_params
current_page = params.get("page", "DomainBasedFolding")

if current_page != "DomainBasedFolding":
    params["page"] = "DomainBasedFolding"
    st.stop()

st.title("Domain Based Folding")
st.write("Welcome to the Domain Based Folding page.")

# ToDo: Insert Next button 
#if st.button("Next"):
#    st.query_params["page"] = "QualityBasedFolding"
#    st.stop()
