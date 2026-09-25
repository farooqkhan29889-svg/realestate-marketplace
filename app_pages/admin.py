"""Admin brokerage: platform stats, all deals, schedule meetings, close deals."""

from datetime import datetime, time

import streamlit as st

from utils import api_client as api

st.title("Admin brokerage", icon=":material/admin_panel_settings:")

current_user = st.session_state.get("user")
if not current_user or current_user.get("role") != "admin":
    st.error("Administrative privileges required.")
    st.stop()


def money(value) -> str:
    try:
        return f"${float(value):,.0f}"
    except (TypeError, ValueError):
        return "-"


# --------------------------------------------------------------------------- #
# Platform stats
# --------------------------------------------------------------------------- #
try:
    stats = api.admin_stats()
except api.ApiError as exc:
    st.error(str(exc))
    stats = {}

if stats:
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Properties", stats.get("total_properties", 0))
    s2.metric("Deal requests", stats.get("total_deals", 0))
    s3.metric("Closed deals", stats.get("closed_deals", 0))
    s4.metric("Commission earned", money(stats.get("total_commission_earned", 0)))
    st.caption(
        f"Commission policy: {stats.get('seller_rate_percent', 1)}% seller + "
        f"{stats.get('buyer_rate_percent', 1)}% buyer"
    )

STATUS_OPTIONS = ["ALL", "PENDING_REVIEW", "MEETING_SCHEDULED", "NEGOTIATION", "DEAL_CLOSED", "CANCELLED"]
status_filter = st.selectbox(
    "Filter by status",
    STATUS_OPTIONS,
    format_func=lambda s: "All deals" if s == "ALL" else s.replace("_", " ").title(),
)

try:
    deals = api.admin_deals(None if status_filter == "ALL" else status_filter)
except api.ApiError as exc:
    st.error(str(exc))
    deals = []

if not deals:
    st.info("No deals in the pipeline.", icon=":material/info:")
    st.stop()

for deal in deals:
    deal_id = deal.get("id")
    status = deal.get("status", "")
    with st.container(border=True):
        hc1, hc2 = st.columns([4, 1])
        with hc1:
            st.markdown(f"**#{deal_id} - {deal.get('property_title', 'Property')}**")
            st.caption(
                f"{deal.get('property_city', '')} - Listed: {money(deal.get('property_price'))} - "
                f"Offer: {money(deal.get('buyer_offered_price'))}"
            )
        with hc2:
            st.badge(
                status.replace("_", " ").title(),
                icon=":material/schedule:",
                color="green" if status == "DEAL_CLOSED" else ("blue" if status == "MEETING_SCHEDULED" else "orange"),
            )

        # Admin always sees both parties' contact (the broker needs it).
        bc, sc = st.columns(2)
        with bc:
            st.markdown("**Buyer (lead)**")
            st.write(deal.get("buyer_name", "-"))
            st.caption(f"{deal.get('buyer_phone', '-')} - {deal.get('buyer_email', '-')}")
        with sc:
            st.markdown("**Seller**")
            st.write(deal.get("seller_name", "-"))
            st.caption(f"{deal.get('seller_phone', '-')} - {deal.get('seller_email', '-')}")

        if deal.get("buyer_message"):
            st.caption(f"Buyer message: {deal.get('buyer_message')}")

        if status != "DEAL_CLOSED":
            with st.expander("Schedule meeting", icon=":material/event_available:"):
                with st.form(f"schedule_{deal_id}"):
                    meeting_type = st.selectbox(
                        "Format",
                        ["ONLINE_VIDEO", "IN_PERSON"],
                        format_func=lambda t: "Online video (Meet/Zoom)"
                        if t == "ONLINE_VIDEO"
                        else "In person (office/property)",
                    )
                    meeting_date = st.date_input("Date", value=datetime.today().date())
                    meeting_time = st.time_input("Time", value=time(15, 0))
                    link = st.text_input(
                        "Meeting link or location",
                        placeholder="https://meet.google.com/xyz-abcd-efg",
                    )
                    notes = st.text_area("Broker notes for both parties")
                    sched_submit = st.form_submit_button(
                        "Schedule and notify both parties", type="primary", icon=":material/send:"
                    )
                if sched_submit:
                    if not link:
                        st.error("Provide a meeting link or location.")
                    else:
                        combined = datetime.combine(meeting_date, meeting_time)
                        try:
                            api.schedule_meeting(
                                deal_id,
                                {
                                    "meeting_type": meeting_type,
                                    "meeting_time": combined.isoformat(),
                                    "meeting_link_or_location": link,
                                    "admin_notes": notes or None,
                                },
                            )
                            st.success("Meeting scheduled. Both parties notified and contact unlocked.")
                            st.rerun()
                        except api.ApiError as exc:
                            st.error(str(exc))

            with st.expander("Close deal and bill 1%", icon=":material/request_quote:"):
                default_price = float(deal.get("buyer_offered_price") or deal.get("property_price") or 0)
                with st.form(f"close_{deal_id}"):
                    agreed_price = st.number_input(
                        "Final agreed closing price ($)",
                        min_value=0.0,
                        step=1000.0,
                        value=default_price,
                    )
                    close_notes = st.text_area("Closing notes / contract reference")
                    close_submit = st.form_submit_button(
                        "Finalize deal", type="primary", icon=":material/check_circle:"
                    )
                if agreed_price > 0:
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Seller 1%", money(agreed_price * 0.01))
                    m2.metric("Buyer 1%", money(agreed_price * 0.01))
                    m3.metric("Total revenue", money(agreed_price * 0.02))
                if close_submit:
                    if agreed_price <= 0:
                        st.error("Enter the final agreed price.")
                    else:
                        try:
                            api.close_deal(
                                deal_id,
                                {"agreed_deal_price": agreed_price, "admin_notes": close_notes or None},
                            )
                            st.success("Deal closed. 1% commission recorded and invoices dispatched.")
                            st.rerun()
                        except api.ApiError as exc:
                            st.error(str(exc))
        else:
            cm1, cm2, cm3 = st.columns(3)
            cm1.metric("Agreed price", money(deal.get("agreed_deal_price")))
            cm2.metric("Seller 1%", money(deal.get("seller_commission_1pct")))
            cm3.metric("Buyer 1%", money(deal.get("buyer_commission_1pct")))
            st.caption(f"Commission status: {deal.get('commission_status', '').replace('_', ' ').title()}")
