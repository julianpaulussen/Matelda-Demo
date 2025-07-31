"""
Common CSS styling components for the application
"""
import streamlit as st


def apply_base_styles():
    """Apply base styles that are common across all pages"""
    st.markdown(
        """
        <style>
            [data-testid="stSidebarNav"] {display: none;}
            /* Keep columns from wrapping on small screens */
            @media (max-width: 768px) {
                div[data-testid="stHorizontalBlock"] {
                    flex-wrap: nowrap;
                    overflow-x: auto;
                }
                div[data-testid="stHorizontalBlock"] > div {
                    min-width: 120px;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def apply_folding_styles():
    """Apply styles specific to domain and quality based folding pages"""
    st.markdown(
        """
        <style>
        div.action-container div[data-testid="stHorizontalBlock"] {
            gap:0 !important;
        }
        div.action-container div[data-testid="column"] {
            padding:0 !important;
        }
        div.action-container button {
            margin:0 !important;
        }
        div[data-testid="baseButton-primary"] > button {
            background-color: #ff4b4b;
            color: white;
        }
        div.fold-row div[data-testid="stHorizontalBlock"],
        div.table-row div[data-testid="stHorizontalBlock"] {
            gap:0 !important;
        }
        div.fold-row div[data-testid="column"],
        div.table-row div[data-testid="column"] {
            padding:0 !important;
        }
        div.fold-row [data-testid="stCheckbox"],
        div.table-row [data-testid="stCheckbox"] {
            margin:0 !important;
        }
        /* Mobile-specific fixes for checkbox spacing */
        @media (max-width: 768px) {
            div.fold-row div[data-testid="column"]:first-child,
            div.table-row div[data-testid="column"]:first-child {
                width: 40px !important;
                min-width: 40px !important;
                max-width: 40px !important;
                flex: 0 0 40px !important;
            }
            div.fold-row div[data-testid="column"]:last-child,
            div.table-row div[data-testid="column"]:last-child {
                flex: 1 !important;
                min-width: auto !important;
            }
            div.fold-row div[data-testid="stHorizontalBlock"],
            div.table-row div[data-testid="stHorizontalBlock"] {
                gap: 8px !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
