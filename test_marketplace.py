import sys
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.user import User

client = TestClient(app)

def run_tests():
    print("=== STARTING MARKETPLACE WORKFLOW TESTS ===")

    # 1. Test Login as Admin, Seller, Buyer
    admin_login = client.post("/api/v1/auth/login", json={"email": "admin@realestate.com", "password": "admin123"})
    assert admin_login.status_code == 200, f"Admin login failed: {admin_login.text}"
    admin_token = admin_login.json()["access_token"]
    print("[OK] Admin login successful")

    seller_login = client.post("/api/v1/auth/login", json={"email": "seller@realestate.com", "password": "seller123"})
    assert seller_login.status_code == 200, f"Seller login failed: {seller_login.text}"
    seller_token = seller_login.json()["access_token"]
    print("[PASS] Seller login successful")

    buyer_login = client.post("/api/v1/auth/login", json={"email": "buyer@realestate.com", "password": "buyer123"})
    assert buyer_login.status_code == 200, f"Buyer login failed: {buyer_login.text}"
    buyer_token = buyer_login.json()["access_token"]
    print("[PASS] Buyer login successful")

    # 2. Seller creates a new property listing for FREE
    new_prop_data = {
        "title": "Oceanfront Sunset Villa with Private Beach Access",
        "description": "Stunning seaside villa with direct private beach access, infinity deck, and floor-to-ceiling glass windows.",
        "price": 1200000.0,
        "property_type": "Villa",
        "listing_type": "Sale",
        "bedrooms": 4,
        "bathrooms": 4,
        "area_sqft": 3600.0,
        "address": "88 Ocean Drive",
        "city": "San Diego",
        "state": "CA",
        "pincode": "92109",
        "amenities": "Private Beach, Pool, Spa, Smart Home, 3-Car Garage"
    }
    create_res = client.post(
        "/api/v1/properties/",
        json=new_prop_data,
        headers={"Authorization": f"Bearer {seller_token}"}
    )
    assert create_res.status_code == 201, f"Create property failed: {create_res.text}"
    prop = create_res.json()
    prop_id = prop["id"]
    print(f"[PASS] Seller listed property #{prop_id} for FREE: '{prop['title']}' (${prop['price']:,.2f})")

    # 3. Buyer browses properties & views detail
    detail_res = client.get(f"/api/v1/properties/{prop_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert "seller_phone" not in detail, "Seller phone must be protected/masked"
    assert "seller_email" not in detail, "Seller email must be protected/masked"
    print(f"[PASS] Buyer viewed property #{prop_id}. Seller phone & email are shielded for 1% commission protection.")

    # 4. Buyer requests a deal meeting (acknowledges 1% fee)
    deal_req_data = {
        "property_id": prop_id,
        "buyer_offered_price": 1150000.0,
        "buyer_message": "Pre-approved mortgage ready. Can we meet online this Friday?",
        "buyer_agreed_1pct_fee": True
    }
    deal_res = client.post(
        "/api/v1/deals/request-meeting",
        json=deal_req_data,
        headers={"Authorization": f"Bearer {buyer_token}"}
    )
    assert deal_res.status_code == 201, f"Deal meeting request failed: {deal_res.text}"
    deal = deal_res.json()
    deal_id = deal["id"]
    assert deal["status"] == "PENDING_REVIEW"
    print(f"[PASS] Buyer requested deal meeting #{deal_id} with offer ${deal['buyer_offered_price']:,.2f} and accepted 1% fee.")

    # 5. Check Notifications generated
    admin_notifs = client.get("/api/v1/notifications/", headers={"Authorization": f"Bearer {admin_token}"}).json()
    assert any(n["is_for_admin"] and "New Buy Request" in n["title"] for n in admin_notifs)
    print("[PASS] Platform Admin received instant Deal Alert notification")

    seller_notifs = client.get("/api/v1/notifications/", headers={"Authorization": f"Bearer {seller_token}"}).json()
    assert any("Deal Alert" in n["title"] for n in seller_notifs)
    print("[PASS] Seller received instant Deal Alert notification")

    # 6. Admin schedules the meeting (Google Meet video conference)
    sched_payload = {
        "meeting_type": "ONLINE_VIDEO",
        "meeting_time": "2026-09-25T15:00:00Z",
        "meeting_link_or_location": "https://meet.google.com/est-deal-9988",
        "admin_notes": "Both parties requested an online introductory negotiation call."
    }
    sched_res = client.post(
        f"/api/v1/admin/deals/{deal_id}/schedule",
        json=sched_payload,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert sched_res.status_code == 200, f"Admin schedule failed: {sched_res.text}"
    sched_deal = sched_res.json()
    assert sched_deal["status"] == "MEETING_SCHEDULED"
    assert sched_deal["meeting_link_or_location"] == "https://meet.google.com/est-deal-9988"
    print(f"[PASS] Admin scheduled meeting for {sched_deal['meeting_time']} with link {sched_deal['meeting_link_or_location']}")

    # 7. Admin conducts meeting, closes deal at agreed $1,180,000, and system calculates 1% commission
    close_payload = {
        "agreed_deal_price": 1180000.0,
        "admin_notes": "Deal agreed during video conference. Purchase contract signed."
    }
    close_res = client.post(
        f"/api/v1/admin/deals/{deal_id}/close",
        json=close_payload,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert close_res.status_code == 200, f"Admin close deal failed: {close_res.text}"
    closed_deal = close_res.json()
    assert closed_deal["status"] == "DEAL_CLOSED"
    assert closed_deal["seller_commission_1pct"] == 11800.0, f"Expected 11800.0, got {closed_deal['seller_commission_1pct']}"
    assert closed_deal["buyer_commission_1pct"] == 11800.0, f"Expected 11800.0, got {closed_deal['buyer_commission_1pct']}"
    assert closed_deal["total_platform_commission"] == 23600.0, f"Expected 23600.0, got {closed_deal['total_platform_commission']}"
    print(f"[PASS] Deal #{deal_id} finalized at ${closed_deal['agreed_deal_price']:,.2f}:")
    print(f"    - Seller 1% Commission: ${closed_deal['seller_commission_1pct']:,.2f}")
    print(f"    - Buyer 1% Commission:  ${closed_deal['buyer_commission_1pct']:,.2f}")
    print(f"    - Total 2% Platform Revenue: ${closed_deal['total_platform_commission']:,.2f}")

    # 8. Check that property is now marked as SOLD
    prop_check = client.get(f"/api/v1/properties/{prop_id}").json()
    assert prop_check["status"] == "sold"
    print(f"[PASS] Property status updated to '{prop_check['status']}'")

    # 9. Admin Stats Check
    stats = client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {admin_token}"}).json()
    assert stats["closed_deals"] >= 1
    assert stats["total_commission_earned"] >= 23600.0
    print(f"[PASS] Platform Brokerage Stats verified: Total Platform Revenue = ${stats['total_commission_earned']:,.2f}")

    print("\n=== ALL WORKFLOW TESTS PASSED PERFECTLY! ===")

if __name__ == "__main__":
    run_tests()
