"""
Theme switcher component for toggling between light and dark themes
"""
import streamlit as st
import shutil
import os
import toml


def load_theme_config(theme_mode):
    """Load theme configuration from theme-specific file"""
    try:
        config_dir = os.path.join(os.path.dirname(__file__), "../.streamlit")
        config_file = os.path.join(config_dir, f"config_{theme_mode}.toml")
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = toml.load(f)
                return config.get('theme', {})
        else:
            # Fallback to default values
            return get_default_theme_config(theme_mode)
    except Exception as e:
        st.error(f"Error loading theme config: {e}")
        return get_default_theme_config(theme_mode)


def get_default_theme_config(theme_mode):
    """Get default theme configuration as fallback"""
    if theme_mode == "dark":
        return {
            "base": "dark",
            "primaryColor": "#f4b11c",
            "backgroundColor": "#0e1117",
            "secondaryBackgroundColor": "#262730",
            "textColor": "#fafafa",
            "font": "monospace"
        }
    else:  # light theme
        return {
            "base": "light",
            "primaryColor": "#f4b11c",
            "backgroundColor": "#e6e6e6",
            "secondaryBackgroundColor": "#ffffff",
            "textColor": "#002f67",
            "font": "monospace"
        }


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
        source_config = os.path.join(config_dir, f"config_{theme_mode}.toml")
        target_config = os.path.join(config_dir, "config.toml")
        
        if os.path.exists(source_config):
            # Copy the theme-specific config file
            shutil.copy2(source_config, target_config)
        else:
            # If theme file doesn't exist, create it dynamically
            theme_config = {
                "theme": get_default_theme_config(theme_mode)
            }
            with open(target_config, 'w') as f:
                toml.dump(theme_config, f)
            
    except Exception as e:
        st.error(f"Error switching theme: {e}")


def get_current_theme():
    """Get the current theme configuration from the active config file"""
    try:
        config_dir = os.path.join(os.path.dirname(__file__), "../.streamlit")
        config_file = os.path.join(config_dir, "config.toml")
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = toml.load(f)
                return config.get('theme', {})
        else:
            # Fallback to light theme if no config exists
            return get_default_theme_config("light")
    except Exception as e:
        # Fallback to light theme on error
        return get_default_theme_config("light")
