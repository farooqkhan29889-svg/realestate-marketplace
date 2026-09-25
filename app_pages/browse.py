"""Public marketplace: search/filter listings, view details, request a meeting."""

import base64
import functools
from pathlib import Path

import streamlit as st

from utils import api_client as api

HERO_IMAGE = Path(__file__).resolve().parent.parent / "assets" / "hero.jpg"
HERO_BG = Path(__file__).resolve().parent.parent / "assets" / "hero_bg.jpg"

PROPERTY_TYPES = ["Apartment", "Villa", "House", "Plot", "Farmhouse", "Land", "Commercial"]


@functools.lru_cache(maxsize=1)
def _background_css() -> str:
    b64 = base64.b64encode(HERO_BG.read_bytes()).decode("ascii")
    return (
        "<style>"
        'section[data-testid="stMain"]{'
        "background-image:"
        "linear-gradient(rgba(255,255,255,0.35),rgba(255,255,255,0.55)),"
        f'url("data:image/jpeg;base64,{b64}");'
        "background-size:cover;"
        "background-position:center;"
        "background-attachment:fixed;"
        "background-repeat:no-repeat;"
        "}"
        "</style>"
    )


st.html(_background_css())

st.session_state.setdefault("filters", {})
st.session_state.setdefault("selected_property_id", None)


def money(value) -> str:
    try:
        return f"${float(value):,.0f}"
    except (TypeError, ValueError):
        return "-"


# --------------------------------------------------------------------------- #
# Detail view
# --------------------------------------------------------------------------- #
selected_id = st.session_state.get("selected_property_id")
if selected_id is not None:
    try:
        prop = api.get_property(selected_id)
    except api.ApiError as exc:
        st.error(str(exc))
        prop = None

    if prop:
        if st.button("Back to results", icon=":material/arrow_back:"):
            st.session_state.selected_property_id = None
            st.rerun()

        st.subheader(prop["title"])
        st.markdown(
            f":material/location_on: {prop.get('address', '')}, {prop.get('city', '')}, "
            f"{prop.get('state', '')} - **{money(prop.get('price'))}**"
        )

        images = [api.absolute_url(img["image_url"]) for img in prop.get("images", []) if img.get("image_url")]
        if images:
            st.image(images, width="stretch")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Type", prop.get("property_type", "-"))
        c2.metric("Bedrooms", prop.get("bedrooms", "-"))
        c3.metric("Bathrooms", prop.get("bathrooms", "-"))
        c4.metric("Area", f"{prop.get('area_sqft', '-')} sqft")

        st.markdown("#### About this property")
        st.write(prop.get("description", ""))

        amenities = prop.get("amenities")
        if amenities:
            st.markdown("#### Amenities")
            for item in [a.strip() for a in amenities.split(",") if a.strip()]:
                st.badge(item, icon=":material/check:", color="green")

        st.markdown("#### Request a deal meeting")
        st.caption(
            "Seller contact stays protected. When you request a meeting, our broker coordinates it "
            "and unlocks direct contact. A 1% facilitation fee applies to each side only if the deal closes."
        )

        current_user = st.session_state.get("user")
        if not current_user:
            st.info("Sign in as a buyer to request a meeting.", icon=":material/login:")
        elif current_user.get("role") not in ("buyer", "admin"):
            st.warning("Only buyer accounts can request a meeting. Sign in with a buyer account.")
        else:
            with st.form("buy_form"):
                offer = st.number_input(
                    "Your offer price ($)",
                    min_value=0.0,
                    step=1000.0,
                    value=float(prop.get("price") or 0.0),
                )
                message = st.text_area("Message or questions for the seller", placeholder="e.g. Cash buyer, available evenings")
                agreed = st.checkbox("I agree to the 1% platform facilitation fee upon a successful purchase.", value=True)
                submit = st.form_submit_button("Request deal meeting", type="primary", icon=":material/event_available:")
            if submit:
                if not agreed:
                    st.error("You must accept the 1% facilitation fee to continue.")
                else:
                    try:
                        api.request_meeting(
                            {
                                "property_id": prop["id"],
                                "buyer_offered_price": offer or prop.get("price"),
                                "buyer_message": message,
                                "buyer_agreed_1pct_fee": True,
                            }
                        )
                        st.success("Meeting request sent! Our broker will arrange the meeting and notify you.")
                    except api.ApiError as exc:
                        st.error(str(exc))
    st.stop()


# --------------------------------------------------------------------------- #
# Search + grid
# --------------------------------------------------------------------------- #
st.image(HERO_IMAGE, width="stretch")
st.title("Find your next home", icon=":material/search:")
st.caption(
    "Browse verified listings for free. Request a meeting and our broker coordinates it - "
    "a 1% facilitation fee applies to each side only when a deal closes."
)

with st.container(border=True):
    with st.form("filters_form"):
        fc1, fc2, fc3, fc4 = st.columns([2, 1, 1, 1])
        q = fc1.text_input("Search", placeholder="City, address or keyword")
        ptype = fc2.selectbox(
            "Property type", [""] + PROPERTY_TYPES, format_func=lambda x: "All types" if x == "" else x
        )
        max_price = fc3.number_input("Max budget ($)", min_value=0, step=50000, value=0)
        beds = fc4.selectbox(
            "Min bedrooms", ["", "1", "2", "3", "4"], format_func=lambda x: "Any beds" if x == "" else f"{x}+ beds"
        )
        applied = st.form_submit_button("Apply filters", icon=":material/filter_list:")

    if applied:
        st.session_state.filters = {
            "q": q,
            "property_type": ptype,
            "max_price": max_price,
            "bedrooms": beds,
        }

filters = st.session_state.get("filters", {})

try:
    properties = api.list_properties(**filters)
except api.ApiError as exc:
    st.error(str(exc))
    properties = []

st.markdown(f"**{len(properties)}** active listings")

if not properties:
    st.info("No properties match your filters.", icon=":material/info:")
    st.stop()

# Responsive grid: 3 cards per row.
for row_start in range(0, len(properties), 3):
    row = properties[row_start : row_start + 3]
    cols = st.columns(3)
    for col, prop in zip(cols, row):
        with col:
            with st.container(border=True):
                images = [img["image_url"] for img in prop.get("images", []) if img.get("image_url")]
                if images:
                    st.image(api.absolute_url(images[0]), width="stretch")
                st.markdown(f"**{prop['title']}**")
                st.caption(f":material/location_on: {prop.get('city', '')}, {prop.get('state', '')}")
                st.markdown(f"**{money(prop.get('price'))}**")
                st.caption(
                    f"{prop.get('bedrooms', 0)} beds - {prop.get('bathrooms', 0)} baths - "
                    f"{prop.get('area_sqft', 0)} sqft"
                )
                if st.button("View details", key=f"view_{prop['id']}", width="stretch"):
                    st.session_state.selected_property_id = prop["id"]
                    st.rerun()
