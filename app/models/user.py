from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class UserRole:
    BUYER = "buyer"
    SELLER = "seller"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(30), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default=UserRole.BUYER, nullable=False)  # buyer, seller, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    properties = relationship("Property", back_populates="seller", cascade="all, delete-orphan")
    buyer_deals = relationship("DealMeetingRequest", foreign_keys="DealMeetingRequest.buyer_id", back_populates="buyer")
    seller_deals = relationship("DealMeetingRequest", foreign_keys="DealMeetingRequest.seller_id", back_populates="seller")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
