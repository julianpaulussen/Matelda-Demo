"""
Theme switcher component for toggling between light and dark themes
"""
import streamlit as st
import shutil
import os


def render_theme_switcher():
    """Render a theme switcher in the sidebar"""
    
    # Initialize theme state if not exists
    if "current_theme" not in st.session_state:
        st.session_state.current_theme = "light"
    
    st.sidebar.markdown("---")
    #st.sidebar.subheader("Theme")
    
    # Theme selection
    theme_options = ["Light", "Dark"]
    current_theme_display = "Light" if st.session_state.current_theme == "light" else "Dark"
    
    selected_theme = st.sidebar.selectbox(
        "Choose theme:",
        options=theme_options,
        index=theme_options.index(current_theme_display),
        key="theme_selector"
    )
    
    new_theme = "light" if selected_theme == "Light" else "dark"
    
    # If theme changed, update the config file
    if new_theme != st.session_state.current_theme:
        st.session_state.current_theme = new_theme
        switch_theme(new_theme)
        st.rerun()


def switch_theme(theme_mode):
    """Switch between light and dark themes by copying the appropriate config file"""
    try:
        config_dir = os.path.join(os.path.dirname(__file__), "../.streamlit")
        
        if theme_mode == "dark":
            source_config = os.path.join(config_dir, "config_dark.toml")
            target_config = os.path.join(config_dir, "config.toml")
        else:
            # For light theme, we'll create a proper light config
            target_config = os.path.join(config_dir, "config.toml")
            light_config_content = """[theme]
base = "light"
primaryColor = "#002f67"
backgroundColor = "#e6e6e6"
secondaryBackgroundColor = "#ffffff"
textColor = "#002f67"
font = "monospace"
"""
            with open(target_config, 'w') as f:
                f.write(light_config_content)
            return
        
        if os.path.exists(source_config):
            shutil.copy2(source_config, target_config)
        else:
            st.error(f"Theme config file not found: {source_config}")
            
    except Exception as e:
        st.error(f"Error switching theme: {e}")


def get_current_theme():
    """Get the current theme mode"""
    return st.session_state.get("current_theme", "light")
