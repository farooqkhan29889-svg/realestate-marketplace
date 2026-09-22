from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.deps import get_current_user, require_buyer, require_seller
from app.models.user import User, UserRole
from app.models.property import Property, PropertyStatus
from app.models.deal_meeting import DealMeetingRequest, DealStatus
from app.models.notification import Notification
from app.schemas.deal_meeting import DealRequestCreate, DealMeetingOut

router = APIRouter(prefix="/deals", tags=["Deals & Meetings"])

def to_deal_out(deal: DealMeetingRequest) -> DealMeetingOut:
    prop = deal.property
    buyer = deal.buyer
    seller = deal.seller
    
    return DealMeetingOut(
        id=deal.id,
        property_id=deal.property_id,
        buyer_id=deal.buyer_id,
        seller_id=deal.seller_id,
        buyer_offered_price=deal.buyer_offered_price,
        buyer_message=deal.buyer_message,
        buyer_agreed_1pct_fee=deal.buyer_agreed_1pct_fee,
        seller_agreed_1pct_fee=deal.seller_agreed_1pct_fee,
        status=deal.status,
        meeting_type=deal.meeting_type,
        meeting_time=deal.meeting_time,
        meeting_link_or_location=deal.meeting_link_or_location,
        admin_notes=deal.admin_notes,
        agreed_deal_price=deal.agreed_deal_price,
        seller_commission_1pct=deal.seller_commission_1pct,
        buyer_commission_1pct=deal.buyer_commission_1pct,
        total_platform_commission=deal.total_platform_commission,
        commission_status=deal.commission_status,
        created_at=deal.created_at,
        updated_at=deal.updated_at,
        property_title=prop.title if prop else None,
        property_city=prop.city if prop else None,
        property_price=prop.price if prop else None,
        buyer_name=buyer.full_name if buyer else None,
        buyer_phone=buyer.phone if buyer else None,
        buyer_email=buyer.email if buyer else None,
        seller_name=seller.full_name if seller else None,
        seller_phone=seller.phone if seller else None,
        seller_email=seller.email if seller else None
    )

@router.post("/request-meeting", response_model=DealMeetingOut, status_code=status.HTTP_201_CREATED)
def request_deal_meeting(
    request_in: DealRequestCreate,
    current_user: User = Depends(require_buyer),
    db: Session = Depends(get_db)
):
    """
    Buyer requests to buy or schedule a deal meeting for a property.
    Acknowledges and accepts the 1% platform facilitation fee upon closing.
    Triggers instant alert notifications to Admin and Seller.
    """
    if not request_in.buyer_agreed_1pct_fee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must accept the 1% platform facilitation commission terms to request a meeting."
        )

    prop = db.query(Property).filter(Property.id == request_in.property_id).first()
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found.")
    
    if prop.seller_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot request to buy your own property.")

    # Check if active request already exists from this buyer
    existing = db.query(DealMeetingRequest).filter(
        DealMeetingRequest.property_id == prop.id,
        DealMeetingRequest.buyer_id == current_user.id,
        DealMeetingRequest.status.in_([DealStatus.PENDING_REVIEW, DealStatus.MEETING_SCHEDULED, DealStatus.NEGOTIATION])
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have an active meeting or deal request for this property."
        )

    deal = DealMeetingRequest(
        property_id=prop.id,
        buyer_id=current_user.id,
        seller_id=prop.seller_id,
        buyer_offered_price=request_in.buyer_offered_price or prop.price,
        buyer_message=request_in.buyer_message,
        buyer_agreed_1pct_fee=True,
        seller_agreed_1pct_fee=True,
        status=DealStatus.PENDING_REVIEW
    )
    db.add(deal)
    db.flush()  # to get deal.id

    # 1. Alert Notification to Platform Admin (lead alert)
    admin_notif = Notification(
        user_id=None,
        is_for_admin=True,
        title=f"New Buy Request Alert: {prop.title}",
        message=f"Buyer '{current_user.full_name}' requested a deal meeting for '{prop.title}' (Listed: ${prop.price:,.2f}, Offered: ${deal.buyer_offered_price:,.2f}). Both parties agreed to 1% fee.",
        link_url=f"/admin/deals/{deal.id}"
    )
    db.add(admin_notif)

    # 2. Alert Notification to Seller
    seller_notif = Notification(
        user_id=prop.seller_id,
        is_for_admin=False,
        title="Deal Alert: Buyer Interested in Your Property!",
        message=f"A qualified buyer has requested a meeting for '{prop.title}'. Our platform team is coordinating the meeting schedule and will notify you with date & video link shortly.",
        link_url=f"/deals/{deal.id}"
    )
    db.add(seller_notif)

    # 3. Confirmation Notification to Buyer
    buyer_notif = Notification(
        user_id=current_user.id,
        is_for_admin=False,
        title="Meeting Request Received!",
        message=f"Your request for '{prop.title}' is with our brokerage team. We will arrange a verified meeting with the seller and send you the link/schedule.",
        link_url=f"/deals/{deal.id}"
    )
    db.add(buyer_notif)

    db.commit()
    db.refresh(deal)
    return to_deal_out(deal)

@router.get("/my-requests", response_model=List[DealMeetingOut])
def get_my_buyer_requests(
    current_user: User = Depends(require_buyer),
    db: Session = Depends(get_db)
):
    deals = db.query(DealMeetingRequest).filter(
        DealMeetingRequest.buyer_id == current_user.id
    ).order_by(DealMeetingRequest.created_at.desc()).all()
    return [to_deal_out(d) for d in deals]

@router.get("/seller-requests", response_model=List[DealMeetingOut])
def get_my_seller_requests(
    current_user: User = Depends(require_seller),
    db: Session = Depends(get_db)
):
    deals = db.query(DealMeetingRequest).filter(
        DealMeetingRequest.seller_id == current_user.id
    ).order_by(DealMeetingRequest.created_at.desc()).all()
    return [to_deal_out(d) for d in deals]

@router.get("/{deal_id}", response_model=DealMeetingOut)
def get_deal_detail(
    deal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    deal = db.query(DealMeetingRequest).filter(DealMeetingRequest.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found.")

    if current_user.role != UserRole.ADMIN and current_user.id not in [deal.buyer_id, deal.seller_id]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    return to_deal_out(deal)
