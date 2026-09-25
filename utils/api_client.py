"""HTTP client for the Real Estate Marketplace FastAPI backend.

The Streamlit app is a thin, pure-Python client. All authentication,
authorization, and contact-shielding logic lives in the FastAPI backend so
there is a single source of truth for security.
"""

from __future__ import annotations

import os

import requests
import streamlit as st

_DEFAULT_BASE = "http://127.0.0.1:8000"
_TIMEOUT = 30


class ApiError(Exception):
    """Raised when the backend returns an error or cannot be reached."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def get_base_url() -> str:
    base = None
    try:
        base = st.secrets.get("api_base_url")  # type: ignore[attr-defined]
    except Exception:
        base = None
    if not base:
        base = os.getenv("API_BASE_URL")
    return (base or _DEFAULT_BASE).rstrip("/")


@st.cache_resource
def _session() -> requests.Session:
    return requests.Session()


def _extract_detail(resp: requests.Response) -> str:
    try:
        payload = resp.json()
    except ValueError:
        return f"HTTP {resp.status_code}"
    if isinstance(payload, dict) and "detail" in payload:
        detail = payload["detail"]
        if isinstance(detail, list):  # FastAPI/pydantic validation errors
            return "; ".join(str(item.get("msg", item)) for item in detail)
        return str(detail)
    return str(payload)


def _request(
    method: str,
    path: str,
    *,
    token: str | None = None,
    json: dict | None = None,
    params: dict | None = None,
    files: list | None = None,
) -> object:
    url = f"{get_base_url()}/api/v1{path}"
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        resp = _session().request(
            method, url, headers=headers, json=json, params=params, files=files, timeout=_TIMEOUT
        )
    except requests.RequestException as exc:
        raise ApiError(
            f"Cannot reach the API at {get_base_url()}. Is the backend running? ({exc})"
        ) from exc

    if resp.status_code >= 400:
        raise ApiError(_extract_detail(resp), resp.status_code)
    if resp.status_code == 204:
        return None
    if "application/json" in resp.headers.get("content-type", ""):
        return resp.json()
    return resp.content


def absolute_url(url: str) -> str:
    """Turn a backend-relative path (e.g. /uploads/x.jpg) into an absolute URL."""
    if not url:
        return url
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return f"{get_base_url()}{url}"


# --------------------------------------------------------------------------- #
# Auth (token + user live in st.session_state, per browser session)
# --------------------------------------------------------------------------- #
def token() -> str | None:
    return st.session_state.get("token")


def user() -> dict | None:
    return st.session_state.get("user")


def login(email: str, password: str) -> dict:
    out = _request("POST", "/auth/login", json={"email": email, "password": password})
    st.session_state["token"] = out["access_token"]
    st.session_state["user"] = out["user"]
    return out["user"]


def register(full_name: str, email: str, phone: str, password: str, role: str) -> dict:
    out = _request(
        "POST",
        "/auth/register",
        json={
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "password": password,
            "role": role,
        },
    )
    st.session_state["token"] = out["access_token"]
    st.session_state["user"] = out["user"]
    return out["user"]


def logout() -> None:
    st.session_state.pop("token", None)
    st.session_state.pop("user", None)


# --------------------------------------------------------------------------- #
# Properties
# --------------------------------------------------------------------------- #
def list_properties(**filters) -> list:
    params = {k: v for k, v in filters.items() if v not in (None, "", 0)}
    return _request("GET", "/properties/", params=params) or []


def get_property(property_id: int) -> dict:
    return _request("GET", f"/properties/{property_id}")


def my_listings() -> list:
    return _request("GET", "/properties/my-listings", token=token()) or []


def create_property(payload: dict) -> dict:
    return _request("POST", "/properties/", token=token(), json=payload)


def upload_images(property_id: int, files: list) -> list:
    """files: list of (filename, bytes, content_type) tuples."""
    multipart = [("files", f) for f in files]
    return _request("POST", f"/properties/{property_id}/images", token=token(), files=multipart) or []


def delete_property(property_id: int) -> None:
    _request("DELETE", f"/properties/{property_id}", token=token())


# --------------------------------------------------------------------------- #
# Deals & meetings
# --------------------------------------------------------------------------- #
def request_meeting(payload: dict) -> dict:
    return _request("POST", "/deals/request-meeting", token=token(), json=payload)


def my_requests() -> list:
    return _request("GET", "/deals/my-requests", token=token()) or []


def seller_requests() -> list:
    return _request("GET", "/deals/seller-requests", token=token()) or []


# --------------------------------------------------------------------------- #
# Admin
# --------------------------------------------------------------------------- #
def admin_deals(status_filter: str | None = None) -> list:
    params = {"status_filter": status_filter} if status_filter else None
    return _request("GET", "/admin/deals", token=token(), params=params) or []


def admin_stats() -> dict:
    return _request("GET", "/admin/stats", token=token())


def schedule_meeting(deal_id: int, payload: dict) -> dict:
    return _request("POST", f"/admin/deals/{deal_id}/schedule", token=token(), json=payload)


def close_deal(deal_id: int, payload: dict) -> dict:
    return _request("POST", f"/admin/deals/{deal_id}/close", token=token(), json=payload)


# --------------------------------------------------------------------------- #
# Notifications
# --------------------------------------------------------------------------- #
def notifications(unread_only: bool = False) -> list:
    return _request("GET", "/notifications/", token=token(), params={"unread_only": unread_only}) or []


def mark_read(notification_id: int) -> None:
    _request("PUT", f"/notifications/{notification_id}/read", token=token())


def mark_all_read() -> None:
    _request("PUT", "/notifications/read-all", token=token())


# --------------------------------------------------------------------------- #
# Misc
# --------------------------------------------------------------------------- #
def meta() -> dict:
    try:
        return _request("GET", "/meta") or {}
    except ApiError:
        return {}
