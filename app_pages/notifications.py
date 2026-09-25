"""Notifications and deal alerts for the signed-in user."""

import streamlit as st

from utils import api_client as api

st.title("Notifications", icon=":material/notifications:")

current_user = st.session_state.get("user")
if not current_user:
    st.warning("Sign in to view your notifications.")
    st.stop()

bar = st.container(horizontal=True)
unread_only = bar.toggle("Unread only", value=False)
if bar.button("Mark all read", icon=":material/done_all:"):
    try:
        api.mark_all_read()
        st.rerun()
    except api.ApiError as exc:
        st.error(str(exc))

try:
    items = api.notifications(unread_only=unread_only)
except api.ApiError as exc:
    st.error(str(exc))
    items = []

if not items:
    st.info("No notifications yet.", icon=":material/info:")
    st.stop()

for note in items:
    with st.container(border=True):
        nc1, nc2 = st.columns([5, 1])
        with nc1:
            st.markdown(f"**{note.get('title', '')}**")
            st.write(note.get("message", ""))
            st.caption(note.get("created_at", ""))
        with nc2:
            if not note.get("is_read"):
                st.badge("New", icon=":material/fiber_new:", color="orange")
                if st.button("Mark read", key=f"read_{note.get('id')}", width="stretch"):
                    try:
                        api.mark_read(note.get("id"))
                        st.rerun()
                    except api.ApiError as exc:
                        st.error(str(exc))
