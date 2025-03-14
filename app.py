import streamlit as st

st.title("Matelda")
st.write("Welcome to Matelda!")
st.markdown("""Read the full paper [here](https://www.openproceedings.org/2025/conf/edbt/paper-98.pdf) or click the button below to continue with configurations.""")

# Next 
if st.button("Start"):
    st.switch_page("pages/Configurations.py")