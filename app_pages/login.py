"""Sign in / create account page."""

from pathlib import Path

import streamlit as st

from utils import api_client as api

HERO_IMAGE = Path(__file__).resolve().parent.parent / "assets" / "hero.jpg"

st.image(HERO_IMAGE, width="stretch")
st.title("Sign in", icon=":material/login:")
st.caption("Listing a property is free. The platform charges a 1% facilitation fee to each side only when a deal closes.")

login_tab, register_tab = st.tabs(["Sign in", "Create account"])

with login_tab:
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", type="primary", icon=":material/login:")
    if submitted:
        if not email or not password:
            st.error("Enter your email and password.")
        else:
            try:
                user = api.login(email.strip(), password)
                st.success(f"Welcome back, {user['full_name']}!")
                st.rerun()
            except api.ApiError as exc:
                st.error(str(exc))

with register_tab:
    with st.form("register_form"):
        full_name = st.text_input("Full name", placeholder="Jane Doe")
        reg_email = st.text_input("Email", placeholder="you@example.com")
        phone = st.text_input("Phone", placeholder="+1 (555) 000-0000")
        role = st.selectbox(
            "I am a",
            ["buyer", "seller"],
            format_func=lambda r: "Buyer (browse and request to buy)"
            if r == "buyer"
            else "Seller / property owner (list free)",
        )
        reg_password = st.text_input("Password", type="password", help="At least 6 characters.")
        reg_submit = st.form_submit_button("Create account", type="primary", icon=":material/person_add:")
    if reg_submit:
        try:
            user = api.register(full_name.strip(), reg_email.strip(), phone.strip(), reg_password, role)
            st.success(f"Account created. Welcome, {user['full_name']}!")
            st.rerun()
        except api.ApiError as exc:
            st.error(str(exc))
