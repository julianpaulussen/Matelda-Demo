import streamlit as st

params = st.query_params
current_page = params.get("page", "Results")

if current_page != "Results":
    params["page"] = "Results"
    st.stop()

st.title("Results")
st.write("Here are the final results!")
