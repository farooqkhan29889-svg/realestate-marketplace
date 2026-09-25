from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.deps import require_admin
from app.core.config import settings
from app.models.user import User, UserRole
from app.models.property import Property, PropertyStatus
from app.models.deal_meeting import DealMeetingRequest, DealStatus
from app.models.notification import Notification
from app.schemas.deal_meeting import DealScheduleUpdate, DealCloseRequest, DealMeetingOut
from app.routers.deals import to_deal_out

router = APIRouter(prefix="/admin", tags=["Platform Admin & Brokerage Operations"])

@router.get("/deals", response_model=List[DealMeetingOut])
def get_all_deals(
    status_filter: Optional[str] = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Platform admin reviews all buy requests and active deals.
    """
    query = db.query(DealMeetingRequest)
    if status_filter:
        query = query.filter(DealMeetingRequest.status == status_filter)
    deals = query.order_by(DealMeetingRequest.created_at.desc()).all()
    return [to_deal_out(d, current_admin) for d in deals]

@router.post("/deals/{deal_id}/schedule", response_model=DealMeetingOut)
def schedule_meeting(
    deal_id: int,
    sched_in: DealScheduleUpdate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Admin schedules the meeting between buyer and seller (Google Meet, Zoom, or office address).
    Notifies both parties immediately with the details.
    """
    deal = db.query(DealMeetingRequest).filter(DealMeetingRequest.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found.")

    deal.status = DealStatus.MEETING_SCHEDULED
    deal.meeting_type = sched_in.meeting_type
    deal.meeting_time = sched_in.meeting_time
    deal.meeting_link_or_location = sched_in.meeting_link_or_location
    deal.admin_notes = sched_in.admin_notes

    # Update property status
    if deal.property:
        deal.property.status = PropertyStatus.MEETING_SCHEDULED

    time_str = sched_in.meeting_time.strftime("%Y-%m-%d %H:%M UTC")

    # Send notification to Buyer
    buyer_notif = Notification(
        user_id=deal.buyer_id,
        is_for_admin=False,
        title=f"Meeting Scheduled: {deal.property.title}",
        message=f"Your deal meeting with the seller is scheduled for {time_str}. Access details: {sched_in.meeting_link_or_location}",
        link_url=f"/deals/{deal.id}"
    )
    db.add(buyer_notif)

    # Send notification to Seller
    seller_notif = Notification(
        user_id=deal.seller_id,
        is_for_admin=False,
        title=f"Buyer Meeting Confirmed: {deal.property.title}",
        message=f"Meeting with interested buyer '{deal.buyer.full_name}' scheduled for {time_str}. Access details: {sched_in.meeting_link_or_location}",
        link_url=f"/deals/{deal.id}"
    )
    db.add(seller_notif)

    db.commit()
    db.refresh(deal)
    return to_deal_out(deal, current_admin)

@router.post("/deals/{deal_id}/close", response_model=DealMeetingOut)
def close_deal_and_calculate_commission(
    deal_id: int,
    close_in: DealCloseRequest,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Admin conducts meeting, finalizes the agreed price, and closes the deal.
    Calculates 1% commission from Seller and 1% commission from Buyer.
    """
    deal = db.query(DealMeetingRequest).filter(DealMeetingRequest.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found.")

    price = close_in.agreed_deal_price
    seller_pct = settings.COMMISSION_PERCENT_SELLER / 100.0
    buyer_pct = settings.COMMISSION_PERCENT_BUYER / 100.0

    seller_comm = round(price * seller_pct, 2)
    buyer_comm = round(price * buyer_pct, 2)
    total_comm = round(seller_comm + buyer_comm, 2)

    deal.agreed_deal_price = price
    deal.seller_commission_1pct = seller_comm
    deal.buyer_commission_1pct = buyer_comm
    deal.total_platform_commission = total_comm
    deal.status = DealStatus.DEAL_CLOSED
    deal.commission_status = "PENDING_PAYMENT"
    if close_in.admin_notes:
        deal.admin_notes = close_in.admin_notes

    # Mark property as sold
    if deal.property:
        deal.property.status = PropertyStatus.SOLD

    # Send notifications
    seller_msg = (
        f"Congratulations! Deal closed for '{deal.property.title}' at ${price:,.2f}. "
        f"Per 1% platform facilitation agreement, seller fee is ${seller_comm:,.2f}."
    )
    db.add(Notification(
        user_id=deal.seller_id,
        is_for_admin=False,
        title="🎉 Deal Closed Successfully!",
        message=seller_msg,
        link_url=f"/deals/{deal.id}"
    ))

    buyer_msg = (
        f"Congratulations on your new property '{deal.property.title}'! Closed at ${price:,.2f}. "
        f"Per 1% platform facilitation agreement, buyer fee is ${buyer_comm:,.2f}."
    )
    db.add(Notification(
        user_id=deal.buyer_id,
        is_for_admin=False,
        title="🎉 Property Purchase Finalized!",
        message=buyer_msg,
        link_url=f"/deals/{deal.id}"
    ))

    db.commit()
    db.refresh(deal)
    return to_deal_out(deal, current_admin)

@router.get("/stats")
def get_platform_stats(
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    total_users = db.query(User).count()
    total_properties = db.query(Property).count()
    total_deals = db.query(DealMeetingRequest).count()
    closed_deals = db.query(DealMeetingRequest).filter(DealMeetingRequest.status == DealStatus.DEAL_CLOSED).count()
    
    total_revenue_result = db.query(func.sum(DealMeetingRequest.total_platform_commission)).filter(
        DealMeetingRequest.status == DealStatus.DEAL_CLOSED
    ).scalar()
    total_platform_commission = total_revenue_result or 0.0

    return {
        "total_users": total_users,
        "total_properties": total_properties,
        "total_deals": total_deals,
        "closed_deals": closed_deals,
        "total_commission_earned": round(total_platform_commission, 2),
        "seller_rate_percent": settings.COMMISSION_PERCENT_SELLER,
        "buyer_rate_percent": settings.COMMISSION_PERCENT_BUYER
    }
