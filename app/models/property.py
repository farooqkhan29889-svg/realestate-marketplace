from sqlalchemy import Column, Integer, String, Float, Numeric, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class PropertyStatus:
    AVAILABLE = "available"
    MEETING_SCHEDULED = "meeting_scheduled"
    UNDER_CONTRACT = "under_contract"
    SOLD = "sold"
    INACTIVE = "inactive"

class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=False)
    price = Column(Numeric(14, 2), nullable=False, index=True)
    property_type = Column(String(50), nullable=False, default="Apartment")  # Apartment, Villa, House, Plot, Commercial
    listing_type = Column(String(20), nullable=False, default="Sale")  # Sale, Rent
    bedrooms = Column(Integer, default=1)
    bathrooms = Column(Integer, default=1)
    area_sqft = Column(Float, nullable=False)
    
    address = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False, index=True)
    state = Column(String(100), nullable=False)
    pincode = Column(String(20), nullable=True)
    amenities = Column(String(500), nullable=True)  # Comma separated e.g. "Swimming Pool, Gym, Parking"

    seller_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(30), default=PropertyStatus.AVAILABLE, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    seller = relationship("User", back_populates="properties")
    images = relationship("PropertyImage", back_populates="property", cascade="all, delete-orphan")
    deal_requests = relationship("DealMeetingRequest", back_populates="property", cascade="all, delete-orphan")


class PropertyImage(Base):
    __tablename__ = "property_images"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    image_url = Column(String(500), nullable=False)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    property = relationship("Property", back_populates="images")
