"""EstateBridge - Streamlit frontend (pure Python).

Entry point. Builds role-based navigation and talks to the FastAPI backend
through utils.api_client. Run with:  streamlit run streamlit_app.py
"""

import streamlit as st

from utils import api_client as api

st.set_page_config(
    page_title="EstateBridge",
    page_icon=":material/apartment:",
    layout="wide",
)

# Per-session auth state (shared across pages).
st.session_state.setdefault("token", None)
st.session_state.setdefault("user", None)

current_user = st.session_state.get("user")

# Build the page list for this user's role.
pages = [
    st.Page("app_pages/browse.py", title="Browse properties", icon=":material/search:"),
]

if current_user:
    role = current_user.get("role")
    if role in ("seller", "admin"):
        pages.append(
            st.Page("app_pages/seller.py", title="Seller portal", icon=":material/home_work:")
        )
    if role in ("buyer", "admin"):
        pages.append(
            st.Page("app_pages/buyer.py", title="My meetings", icon=":material/event:")
        )
    if role == "admin":
        pages.append(
            st.Page("app_pages/admin.py", title="Admin brokerage", icon=":material/admin_panel_settings:")
        )
    pages.append(
        st.Page("app_pages/notifications.py", title="Notifications", icon=":material/notifications:")
    )
else:
    pages.append(st.Page("app_pages/login.py", title="Sign in", icon=":material/login:"))

# Sidebar: brand + auth status.
with st.sidebar:
    st.markdown("## EstateBridge")
    st.caption("Free listings - brokered meetings - 1% facilitation fee")
    if current_user:
        st.markdown(f"**{current_user.get('full_name', '')}**")
        st.badge(current_user.get("role", "").capitalize(), icon=":material/person:", color="blue")
        if st.button("Sign out", icon=":material/logout:", width="stretch"):
            api.logout()
            st.rerun()
    else:
        st.info(
            "Sign in to request meetings, list a property, or manage deals.",
            icon=":material/info:",
        )

nav = st.navigation(pages, position="sidebar")
nav.run()
