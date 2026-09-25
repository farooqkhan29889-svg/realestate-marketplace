from sqlalchemy import Column, Integer, String, Numeric, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class DealStatus:
    PENDING_REVIEW = "PENDING_REVIEW"           # Buyer requested, waiting for admin to schedule
    MEETING_SCHEDULED = "MEETING_SCHEDULED"     # Meeting set with date, time, and link/address
    NEGOTIATION = "NEGOTIATION"                 # Meeting conducted, price being finalized
    DEAL_CLOSED = "DEAL_CLOSED"                 # Deal finalized, 1% commission payable
    CANCELLED = "CANCELLED"                     # Buyer or Seller backed out

class MeetingType:
    ONLINE_VIDEO = "ONLINE_VIDEO"
    IN_PERSON = "IN_PERSON"

class DealMeetingRequest(Base):
    __tablename__ = "deal_meetings"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    buyer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    seller_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Buyer initial offer & notes
    buyer_offered_price = Column(Numeric(14, 2), nullable=True)
    buyer_message = Column(Text, nullable=True)
    
    # 1% platform fee acknowledgments
    buyer_agreed_1pct_fee = Column(Boolean, default=True, nullable=False)
    seller_agreed_1pct_fee = Column(Boolean, default=True, nullable=False)

    # Deal & Meeting Workflow
    status = Column(String(40), default=DealStatus.PENDING_REVIEW, nullable=False, index=True)
    meeting_type = Column(String(30), default=MeetingType.ONLINE_VIDEO)
    meeting_time = Column(DateTime, nullable=True)
    meeting_link_or_location = Column(String(500), nullable=True)
    admin_notes = Column(Text, nullable=True)

    # 1% Commission Financial Tracking (Calculated upon deal closure)
    agreed_deal_price = Column(Numeric(14, 2), nullable=True)
    seller_commission_1pct = Column(Numeric(14, 2), nullable=True)
    buyer_commission_1pct = Column(Numeric(14, 2), nullable=True)
    total_platform_commission = Column(Numeric(14, 2), nullable=True)
    commission_status = Column(String(30), default="UNPAID") # UNPAID, COLLECTED

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    property = relationship("Property", back_populates="deal_requests")
    buyer = relationship("User", foreign_keys=[buyer_id], back_populates="buyer_deals")
    seller = relationship("User", foreign_keys=[seller_id], back_populates="seller_deals")
