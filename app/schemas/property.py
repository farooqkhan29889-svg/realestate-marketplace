from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class PropertyImageOut(BaseModel):
    id: int
    image_url: str
    is_primary: bool

    class Config:
        from_attributes = True

class PropertyCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10)
    price: float = Field(..., gt=0)
    property_type: str = "Apartment"  # Apartment, Villa, House, Plot, Commercial
    listing_type: str = "Sale"        # Sale, Rent
    bedrooms: int = Field(1, ge=0)
    bathrooms: int = Field(1, ge=0)
    area_sqft: float = Field(..., gt=0)
    address: str
    city: str
    state: str
    pincode: Optional[str] = None
    amenities: Optional[str] = None  # e.g. "Parking, Gym, Swimming Pool, Lift"

class PropertyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    property_type: Optional[str] = None
    listing_type: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    area_sqft: Optional[float] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    amenities: Optional[str] = None
    status: Optional[str] = None

class PropertyOut(BaseModel):
    id: int
    title: str
    description: str
    price: float
    property_type: str
    listing_type: str
    bedrooms: int
    bathrooms: int
    area_sqft: float
    address: str
    city: str
    state: str
    pincode: Optional[str] = None
    amenities: Optional[str] = None
    status: str
    is_active: bool
    created_at: datetime
    images: List[PropertyImageOut] = []
    
    # Shielded seller information: Name is shown, but phone/email is protected
    seller_id: int
    seller_name: Optional[str] = None
    
    class Config:
        from_attributes = True
