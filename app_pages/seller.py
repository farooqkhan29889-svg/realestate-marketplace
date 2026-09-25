"""Seller portal: list properties for free, manage listings, see buyer meeting requests."""

import streamlit as st

from utils import api_client as api

st.title("Seller portal", icon=":material/home_work:")

current_user = st.session_state.get("user")
if not current_user or current_user.get("role") not in ("seller", "admin"):
    st.warning("Sign in with a seller account to manage your listings.")
    st.stop()

st.caption("Listing is free. The platform charges a 1% facilitation fee only when a deal closes.")

PROPERTY_TYPES = ["Apartment", "Villa", "House", "Plot", "Farmhouse", "Land", "Commercial"]


def money(value) -> str:
    try:
        return f"${float(value):,.0f}"
    except (TypeError, ValueError):
        return "-"


# --------------------------------------------------------------------------- #
# Add a new listing
# --------------------------------------------------------------------------- #
with st.expander("Add a new listing (free)", icon=":material/add_home_work:"):
    with st.form("listing_form"):
        title = st.text_input("Property title", placeholder="e.g. Modern 3-bedroom villa with pool")
        c1, c2, c3 = st.columns(3)
        price = c1.number_input("Price ($)", min_value=0.0, step=10000.0, value=0.0)
        ptype = c2.selectbox("Type", PROPERTY_TYPES)
        area = c3.number_input("Area (sqft)", min_value=0.0, step=100.0, value=0.0)

        c4, c5, c6, c7 = st.columns(4)
        bedrooms = c4.number_input("Bedrooms", min_value=0, step=1, value=2)
        bathrooms = c5.number_input("Bathrooms", min_value=0, step=1, value=2)
        city = c6.text_input("City", placeholder="Miami")
        state = c7.text_input("State", placeholder="FL")

        address = st.text_input("Full street address", placeholder="123 Palm Ave")
        amenities = st.text_input("Amenities (comma-separated)", placeholder="Pool, Gym, Parking")
        description = st.text_area("Description", placeholder="Describe the property...")
        photos = st.file_uploader(
            "Photos",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=True,
            help=f"Up to 10 images, {5} MB each.",
        )
        submit = st.form_submit_button("Publish listing", type="primary", icon=":material/upload:")

    if submit:
        if not title or price <= 0 or area <= 0 or not city or not state or not address or not description:
            st.error("Fill in all required fields (title, price, area, city, state, address, description).")
        else:
            try:
                payload = {
                    "title": title,
                    "description": description,
                    "price": price,
                    "property_type": ptype,
                    "listing_type": "Sale",
                    "bedrooms": bedrooms,
                    "bathrooms": bathrooms,
                    "area_sqft": area,
                    "address": address,
                    "city": city,
                    "state": state,
                    "amenities": amenities or None,
                }
                created = api.create_property(payload)
                if photos:
                    files = [
                        (p.name, p.getvalue(), p.type or "image/jpeg")
                        for p in photos
                    ]
                    api.upload_images(created["id"], files)
                st.success("Listing published!")
                st.rerun()
            except api.ApiError as exc:
                st.error(str(exc))

# --------------------------------------------------------------------------- #
# My listings
# --------------------------------------------------------------------------- #
st.subheader("My listings", icon=":material/home:")
try:
    listings = api.my_listings()
except api.ApiError as exc:
    st.error(str(exc))
    listings = []

if not listings:
    st.info("You have no listings yet. Add one above - it's free.", icon=":material/info:")
else:
    for prop in listings:
        with st.container(border=True):
            lc, rc = st.columns([4, 1])
            with lc:
                st.markdown(f"**{prop['title']}**")
                st.caption(
                    f"{prop.get('city', '')}, {prop.get('state', '')} - {money(prop.get('price'))} - "
                    f"{prop.get('area_sqft', 0)} sqft"
                )
            with rc:
                st.badge(prop.get("status", "").replace("_", " ").title(), icon=":material/sell:", color="blue")
                if st.button("Delete", key=f"del_{prop['id']}", icon=":material/delete:"):
                    try:
                        api.delete_property(prop["id"])
                        st.toast("Listing deleted.")
                        st.rerun()
                    except api.ApiError as exc:
                        st.error(str(exc))

# --------------------------------------------------------------------------- #
# Incoming buyer meeting requests
# --------------------------------------------------------------------------- #
st.subheader("Incoming buyer meetings", icon=":material/event:")
try:
    deals = api.seller_requests()
except api.ApiError as exc:
    st.error(str(exc))
    deals = []

if not deals:
    st.info("No buyer meeting requests yet.", icon=":material/info:")
else:
    for deal in deals:
        with st.container(border=True):
            dc1, dc2 = st.columns([3, 1])
            with dc1:
                st.markdown(f"**{deal.get('property_title', 'Property')}**")
                st.caption(
                    f"Buyer: {deal.get('buyer_name', 'Buyer')} - "
                    f"Offer: {money(deal.get('buyer_offered_price'))}"
                )
            with dc2:
                st.badge(
                    deal.get("status", "").replace("_", " ").title(),
                    icon=":material/schedule:",
                    color="green" if deal.get("status") == "MEETING_SCHEDULED" else "orange",
                )

            if deal.get("contact_unlocked") and deal.get("buyer_phone"):
                st.success(
                    f"Buyer contact unlocked: {deal.get('buyer_name')} - {deal.get('buyer_phone')}",
                    icon=":material/contact_phone:",
                )
            else:
                st.caption(
                    ":material/lock: Buyer contact unlocks once the broker schedules the meeting."
                )

            if deal.get("meeting_time"):
                st.markdown(
                    f"**Meeting:** {deal.get('meeting_time')}  \n"
                    f"**Access:** {deal.get('meeting_link_or_location', '')}"
                )
