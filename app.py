import streamlit as st

st.title("Matelda")
st.write("Welcome to Matelda! Click the button below to continue to Configurations.")

# ToDo: Insert Next button 
if st.button("Next"):
    st.switch_page("pages/Configurations.py")