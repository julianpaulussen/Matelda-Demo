import streamlit as st
import pandas as pd
import numpy as np

# -------------------- STATE MANAGEMENT --------------------
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "history" not in st.session_state:
    st.session_state.history = []  # Stores liked/disliked indices
if "actions" not in st.session_state:
    st.session_state.actions = []  # Stores actions for undoing

# -------------------- TABLE DATA --------------------
# Generate a sample dataframe
np.random.seed(42)
df = pd.DataFrame(np.random.randint(1, 100, size=(10, 10)), 
                  columns=[f"Col {i}" for i in range(10)])

# -------------------- FUNCTION TO DISPLAY A SUBSET --------------------
def render_card(index):
    if index >= len(df):
        st.write("No more data to display!")
        return
    
    table_size = 5  # Show only a 5x5 section
    row_start = max(0, index - 2)
    row_end = min(len(df), row_start + table_size)
    
    # Select a sub-table
    sub_df = df.iloc[row_start:row_end, :table_size]

    # Highlight a specific cell (center)
    highlighted_row = min(2, len(sub_df) - 1)
    highlighted_col = 2

    def highlight_cell(val):
        return 'background-color: black; color: white' if val == sub_df.iloc[highlighted_row, highlighted_col] else \
               'background-color: lightgray' if val in sub_df.iloc[highlighted_row] or val in sub_df.iloc[:, highlighted_col] else ''

    st.write(f"### Card {index+1} of {len(df)}")
    st.dataframe(sub_df.style.map(highlight_cell))

# -------------------- SWIPE ACTIONS --------------------
def like():
    if st.session_state.current_index < len(df):
        st.session_state.history.append(st.session_state.current_index)
        st.session_state.actions.append("like")
        st.session_state.current_index += 1

def dislike():
    if st.session_state.current_index < len(df):
        st.session_state.history.append(st.session_state.current_index)
        st.session_state.actions.append("dislike")
        st.session_state.current_index += 1

def undo():
    if st.session_state.history:
        last_index = st.session_state.history.pop()
        st.session_state.actions.pop()
        st.session_state.current_index = last_index

# -------------------- UI LAYOUT --------------------
st.title("Quality Based Folding")

# Render the current table card
render_card(st.session_state.current_index)

# Swipe Buttons
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("❌ Dislike", use_container_width=True):
        dislike()
with col2:
    if st.button("↩️ Undo", use_container_width=True):
        undo()
with col3:
    if st.button("✅ Like", use_container_width=True):
        like()
