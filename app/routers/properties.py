import shutil
import uuid
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.core.config import settings
from app.core.deps import get_current_user, require_seller, get_optional_current_user
from app.models.user import User, UserRole
from app.models.property import Property, PropertyImage, PropertyStatus
from app.schemas.property import PropertyCreate, PropertyUpdate, PropertyOut, PropertyImageOut

router = APIRouter(prefix="/properties", tags=["Properties"])

def to_property_out(prop: Property) -> PropertyOut:
    return PropertyOut(
        id=prop.id,
        title=prop.title,
        description=prop.description,
        price=prop.price,
        property_type=prop.property_type,
        listing_type=prop.listing_type,
        bedrooms=prop.bedrooms,
        bathrooms=prop.bathrooms,
        area_sqft=prop.area_sqft,
        address=prop.address,
        city=prop.city,
        state=prop.state,
        pincode=prop.pincode,
        amenities=prop.amenities,
        status=prop.status,
        is_active=prop.is_active,
        created_at=prop.created_at,
        seller_id=prop.seller_id,
        seller_name=prop.seller.full_name if prop.seller else "Verified Seller",
        images=[PropertyImageOut.model_validate(img) for img in prop.images]
    )

@router.post("/", response_model=PropertyOut, status_code=status.HTTP_201_CREATED)
def create_property(
    prop_in: PropertyCreate,
    current_user: User = Depends(require_seller),
    db: Session = Depends(get_db)
):
    """
    Sellers can list properties for FREE.
    Sellers agree that upon a platform-facilitated closing, a 1% commission is payable.
    """
    new_prop = Property(
        title=prop_in.title,
        description=prop_in.description,
        price=prop_in.price,
        property_type=prop_in.property_type,
        listing_type=prop_in.listing_type,
        bedrooms=prop_in.bedrooms,
        bathrooms=prop_in.bathrooms,
        area_sqft=prop_in.area_sqft,
        address=prop_in.address,
        city=prop_in.city,
        state=prop_in.state,
        pincode=prop_in.pincode,
        amenities=prop_in.amenities,
        seller_id=current_user.id,
        status=PropertyStatus.AVAILABLE
    )
    db.add(new_prop)
    db.commit()
    db.refresh(new_prop)
    return to_property_out(new_prop)

@router.post("/{property_id}/images", response_model=List[PropertyImageOut])
def upload_property_images(
    property_id: int,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(require_seller),
    db: Session = Depends(get_db)
):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found.")
    
    # Only the owner or admin can upload photos
    if prop.seller_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to edit this listing.")

    uploaded_images = []
    has_primary = db.query(PropertyImage).filter(PropertyImage.property_id == property_id, PropertyImage.is_primary == True).first() is not None

    for idx, file in enumerate(files):
        ext = Path(file.filename or "image.jpg").suffix.lower()
        if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
            ext = ".jpg"
        
        file_name = f"prop_{property_id}_{uuid.uuid4().hex[:10]}{ext}"
        destination = settings.UPLOAD_DIR / file_name

        with open(destination, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        image_url = f"/uploads/{file_name}"
        is_primary = not has_primary and idx == 0
        if is_primary:
            has_primary = True

        img_record = PropertyImage(
            property_id=property_id,
            image_url=image_url,
            is_primary=is_primary
        )
        db.add(img_record)
        uploaded_images.append(img_record)

    db.commit()
    for img in uploaded_images:
        db.refresh(img)

    return [PropertyImageOut.model_validate(img) for img in uploaded_images]

@router.get("/", response_model=List[PropertyOut])
def list_properties(
    q: Optional[str] = Query(None, description="Search term for title, description, or address"),
    city: Optional[str] = Query(None, description="Filter by city"),
    property_type: Optional[str] = Query(None, description="Apartment, Villa, House, Plot, Commercial"),
    listing_type: Optional[str] = Query(None, description="Sale or Rent"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    bedrooms: Optional[int] = Query(None, description="Number of bedrooms"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(Property).filter(Property.is_active == True)

    if q:
        search_fmt = f"%{q}%"
        query = query.filter(
            or_(
                Property.title.ilike(search_fmt),
                Property.description.ilike(search_fmt),
                Property.address.ilike(search_fmt),
                Property.city.ilike(search_fmt)
            )
        )
    if city:
        query = query.filter(Property.city.ilike(f"%{city}%"))
    if property_type:
        query = query.filter(Property.property_type.ilike(property_type))
    if listing_type:
        query = query.filter(Property.listing_type.ilike(listing_type))
    if min_price is not None:
        query = query.filter(Property.price >= min_price)
    if max_price is not None:
        query = query.filter(Property.price <= max_price)
    if bedrooms is not None:
        query = query.filter(Property.bedrooms >= bedrooms)

    props = query.order_by(Property.created_at.desc()).offset(skip).limit(limit).all()
    return [to_property_out(p) for p in props]

@router.get("/my-listings", response_model=List[PropertyOut])
def get_my_listings(
    current_user: User = Depends(require_seller),
    db: Session = Depends(get_db)
):
    props = db.query(Property).filter(Property.seller_id == current_user.id).order_by(Property.created_at.desc()).all()
    return [to_property_out(p) for p in props]

@router.get("/{property_id}", response_model=PropertyOut)
def get_property_detail(
    property_id: int,
    db: Session = Depends(get_db)
):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found.")
    return to_property_out(prop)

@router.put("/{property_id}", response_model=PropertyOut)
def update_property(
    property_id: int,
    prop_in: PropertyUpdate,
    current_user: User = Depends(require_seller),
    db: Session = Depends(get_db)
):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found.")
    if prop.seller_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to edit this listing.")

    update_data = prop_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(prop, field, val)

    db.commit()
    db.refresh(prop)
    return to_property_out(prop)

@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_property(
    property_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found.")
    if prop.seller_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this listing.")

    db.delete(prop)
    db.commit()
    return None
