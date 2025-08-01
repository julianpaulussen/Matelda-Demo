import os
import streamlit.components.v1 as components

_component_func = components.declare_component(
    "realtime_slider",
    path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend"),
)

def realtime_slider(key: str, min_value: int = 0, max_value: int = 100, value: int = 0):
    """A slider that updates in real time using Streamlit components."""
    return _component_func(
        key=key,
        default=value,
        min_value=min_value,
        max_value=max_value,
        value=value,
    )
