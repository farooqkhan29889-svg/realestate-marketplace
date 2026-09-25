from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.schemas.property import PropertyOut
from app.schemas.user import UserOut

class DealRequestCreate(BaseModel):
    property_id: int
    buyer_offered_price: Optional[float] = None
    buyer_message: Optional[str] = None
    buyer_agreed_1pct_fee: bool = Field(True, description="Buyer agrees to 1% platform fee upon successful closing")

class DealScheduleUpdate(BaseModel):
    meeting_type: str = "ONLINE_VIDEO"  # ONLINE_VIDEO or IN_PERSON
    meeting_time: datetime
    meeting_link_or_location: str
    admin_notes: Optional[str] = None

class DealCloseRequest(BaseModel):
    agreed_deal_price: float = Field(..., gt=0, description="Final agreed transaction price")
    admin_notes: Optional[str] = None

class DealMeetingOut(BaseModel):
    id: int
    property_id: int
    buyer_id: int
    seller_id: int
    buyer_offered_price: Optional[float] = None
    buyer_message: Optional[str] = None
    buyer_agreed_1pct_fee: bool
    seller_agreed_1pct_fee: bool
    status: str
    meeting_type: Optional[str] = None
    meeting_time: Optional[datetime] = None
    meeting_link_or_location: Optional[str] = None
    admin_notes: Optional[str] = None
    agreed_deal_price: Optional[float] = None
    seller_commission_1pct: Optional[float] = None
    buyer_commission_1pct: Optional[float] = None
    total_platform_commission: Optional[float] = None
    commission_status: str
    created_at: datetime
    updated_at: datetime

    # True once the platform has scheduled/approved the meeting, at which point
    # counterparty contact details are released to the other party.
    contact_unlocked: bool = False

    # Embedded summary details
    property_title: Optional[str] = None
    property_city: Optional[str] = None
    property_price: Optional[float] = None
    buyer_name: Optional[str] = None
    # buyer/seller phone & email are only populated for authorized viewers
    # (always for admin; for the counterparty only after contact_unlocked).
    buyer_phone: Optional[str] = None
    buyer_email: Optional[str] = None
    seller_name: Optional[str] = None
    seller_phone: Optional[str] = None
    seller_email: Optional[str] = None

    class Config:
        from_attributes = True
