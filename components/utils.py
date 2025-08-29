"""
Common utility functions used across pages
"""
import pandas as pd
import os
import json
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import streamlit as st


def get_datasets_path(selected_dataset: str) -> str:
    """Get the path to the datasets directory"""
    # Get the root directory (go up from components to project root)
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root_dir, "datasets", selected_dataset)


def load_clean_table(table_name: str, datasets_path: str) -> pd.DataFrame:
    """Load clean.csv file for a given table"""
    file_path = os.path.join(datasets_path, table_name, "clean.csv")
    try:
        return pd.read_csv(file_path)
    except Exception as e:
        return pd.DataFrame({"Error": [f"Could not load {file_path}: {e}"]})


def load_pipeline_config(pipeline_path: str) -> Dict[str, Any]:
    """Load pipeline configuration from JSON file"""
    config_path = os.path.join(pipeline_path, "configurations.json")
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    return {}


def save_pipeline_config(pipeline_path: str, config: Dict[str, Any]) -> None:
    """Save pipeline configuration to JSON file"""
    config_path = os.path.join(pipeline_path, "configurations.json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)


def update_domain_folds_in_config(pipeline_path: str, table_locations: Dict[str, str]) -> bool:
    """Update domain folds in pipeline configuration and return success status"""
    try:
        config = load_pipeline_config(pipeline_path)
        
        # Convert table_locations to domain_folds format
        domain_folds = {}
        for table, fold in table_locations.items():
            domain_folds.setdefault(fold, []).append(table)
        
        config["domain_folds"] = domain_folds
        save_pipeline_config(pipeline_path, config)
        return True
    except Exception as e:
        print(f"Error saving domain folds: {e}")
        return False


# ----------------------------
# Pipeline change tracking
# ----------------------------
def mark_pipeline_dirty() -> None:
    """Mark current session's pipeline state as dirty (changes made)."""
    st.session_state["pipeline_dirty"] = True


def mark_pipeline_clean() -> None:
    """Mark current session's pipeline state as clean (results saved)."""
    st.session_state["pipeline_dirty"] = False


def is_pipeline_dirty() -> bool:
    """Check if current session's pipeline state is dirty."""
    return bool(st.session_state.get("pipeline_dirty", False))


# ----------------------------
# URL utilities
# ----------------------------
def _normalize_url(value: str) -> Optional[str]:
    """Normalize a potentially partial URL string into a full origin.

    - Adds scheme if missing (defaults to https).
    - Returns only the origin (scheme://host[:port]).
    """
    if not value:
        return None
    v = value.strip().strip('/')
    if not v:
        return None
    # Prepend scheme if missing
    if not v.startswith("http://") and not v.startswith("https://"):
        v = "https://" + v
    try:
        parsed = urlparse(v)
        if not parsed.scheme or not parsed.netloc:
            return None
        origin = f"{parsed.scheme}://{parsed.netloc}"
        return origin
    except Exception:
        return None


def get_base_url() -> str:
    """Best-effort detection of the app's base URL (origin).

    Priority:
    1) Use JavaScript `window.location.origin` if available (via streamlit_javascript).
    2) Respect explicit configuration: `st.secrets['base_url']` or common env vars.
    3) Fallback to localhost with the configured Streamlit server port.
    """
    # 1) Attempt to read from browser via JS
    try:
        from streamlit_javascript import st_javascript  # type: ignore
        origin = st_javascript("window.location.origin")
        if isinstance(origin, str) and origin:
            norm = _normalize_url(origin)
            if norm:
                return norm
    except Exception:
        pass

    # 2) Explicit config via secrets or environment
    try:
        base_from_secret = st.secrets.get("base_url")  # type: ignore[attr-defined]
        norm = _normalize_url(str(base_from_secret)) if base_from_secret else None
        if norm:
            return norm
    except Exception:
        pass

    for key in (
        "STREAMLIT_BASE_URL",
        "BASE_URL",
        "PUBLIC_BASE_URL",
        "PUBLIC_URL",
        "EXTERNAL_URL",
        "RENDER_EXTERNAL_URL",
        "VERCEL_URL",
        "FLY_APP_URL",
    ):
        v = os.environ.get(key)
        norm = _normalize_url(v) if v else None
        if norm:
            return norm

    # 3) Fallback to localhost with configured port
    try:
        port = st.get_option("server.port") or 8501
    except Exception:
        port = 8501
    return f"http://localhost:{port}"
