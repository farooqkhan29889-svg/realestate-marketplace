"""Buyer portal: track deal requests, meetings, and unlocked seller contact."""

import streamlit as st

from utils import api_client as api

st.title("My meetings", icon=":material/event:")

current_user = st.session_state.get("user")
if not current_user:
    st.warning("Sign in as a buyer to view your meeting requests.")
    st.stop()


def money(value) -> str:
    try:
        return f"${float(value):,.0f}"
    except (TypeError, ValueError):
        return "-"


try:
    deals = api.my_requests()
except api.ApiError as exc:
    st.error(str(exc))
    deals = []

if not deals:
    st.info(
        "You haven't requested any meetings yet. Browse properties and request a deal meeting.",
        icon=":material/info:",
    )
    st.stop()

STATUS_COLOR = {
    "PENDING_REVIEW": "orange",
    "MEETING_SCHEDULED": "blue",
    "NEGOTIATION": "blue",
    "DEAL_CLOSED": "green",
    "CANCELLED": "red",
}

for deal in deals:
    status = deal.get("status", "")
    with st.container(border=True):
        hc1, hc2 = st.columns([4, 1])
        with hc1:
            st.markdown(f"**{deal.get('property_title', 'Property')}**")
            st.caption(
                f"{deal.get('property_city', '')} - Listed: {money(deal.get('property_price'))} - "
                f"Your offer: {money(deal.get('buyer_offered_price'))}"
            )
        with hc2:
            st.badge(
                status.replace("_", " ").title(),
                icon=":material/schedule:",
                color=STATUS_COLOR.get(status, "gray"),
            )

        if deal.get("meeting_time"):
            st.success(
                f"Meeting scheduled: {deal.get('meeting_time')}",
                icon=":material/event_available:",
            )
            st.markdown(f"**Access / location:** {deal.get('meeting_link_or_location', '')}")
        else:
            st.caption(":material/hourglass_top: Meeting pending broker scheduling.")

        # Contact shielding: seller contact appears only once unlocked.
        if deal.get("contact_unlocked") and deal.get("seller_phone"):
            st.info(
                f"Seller contact (unlocked by broker): {deal.get('seller_name')} - "
                f"{deal.get('seller_phone')} - {deal.get('seller_email', '')}",
                icon=":material/contact_phone:",
            )
        else:
            st.caption(
                ":material/lock: Seller contact stays protected until the broker schedules your meeting."
            )

        if status == "DEAL_CLOSED":
            st.balloons()
            m1, m2, m3 = st.columns(3)
            m1.metric("Agreed price", money(deal.get("agreed_deal_price")))
            m2.metric("Your 1% fee", money(deal.get("buyer_commission_1pct")))
            m3.metric("Status", deal.get("commission_status", "").replace("_", " ").title())
