import os

from sqlalchemy.orm import Session
from app.core.database import Base, engine, SessionLocal
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models.user import User, UserRole
from app.models.property import Property, PropertyImage, PropertyStatus
from app.models.deal_meeting import DealMeetingRequest, DealStatus
from app.models.notification import Notification

_WEAK_LEGACY_ADMIN_PASSWORD = "admin123"


def init_db():
    # Create all tables
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        _bootstrap_admin(db)

        # Demo seed data only exists outside production.
        if not settings.DEMO_MODE:
            return

        # Skip if demo data already present.
        if db.query(User).filter(User.email == "seller@realestate.com").first():
            return

        _seed_demo_data(db)
    finally:
        db.close()


def _bootstrap_admin(db: Session) -> None:
    """Create (or repair) the platform admin from environment variables.

    Never uses a hardcoded default password. If ADMIN_PASSWORD is unset, a
    strong random one is generated and printed to the server console once.
    """
    admin = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()

    if not admin:
        admin = User(
            full_name="Platform Admin / Broker",
            email=settings.ADMIN_EMAIL,
            phone=os.getenv("ADMIN_PHONE", "+1 (555) 019-2831"),
            hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
            role=UserRole.ADMIN,
        )
        db.add(admin)
        db.commit()
        if not os.getenv("ADMIN_PASSWORD"):
            print(
                "\n[SECURITY] No ADMIN_PASSWORD set. Generated a temporary password for "
                f"'{settings.ADMIN_EMAIL}':\n  {settings.ADMIN_PASSWORD}\n"
                "Set ADMIN_PASSWORD in your environment to control this value.\n"
            )
    elif verify_password(_WEAK_LEGACY_ADMIN_PASSWORD, admin.hashed_password):
        # Upgrade an existing account that still uses the old insecure default.
        admin.hashed_password = get_password_hash(settings.ADMIN_PASSWORD)
        db.commit()
        print(
            f"\n[SECURITY] Reset the weak default password for '{settings.ADMIN_EMAIL}'.\n"
            f"  New password: {settings.ADMIN_PASSWORD}\n"
            "Set ADMIN_PASSWORD in your environment to control this value.\n"
        )


def _seed_demo_data(db: Session) -> None:
    seller = User(
        full_name="David Miller (Seller)",
        email="seller@realestate.com",
        phone="+1 (555) 234-5678",
        hashed_password=get_password_hash("seller123"),
        role=UserRole.SELLER,
    )
    db.add(seller)

    buyer = User(
        full_name="Emily Davis (Buyer)",
        email="buyer@realestate.com",
        phone="+1 (555) 876-5432",
        hashed_password=get_password_hash("buyer123"),
        role=UserRole.BUYER,
    )
    db.add(buyer)
    db.flush()

    prop1 = Property(
        title="Luxury 3BHK Penthouse with Skyline View",
        description="Ultra-luxury penthouse featuring panoramic skyline views, private terrace, modern Italian kitchen, and smart home automation. Building amenities include infinity swimming pool, 24/7 concierge, spa, and 2 dedicated parking bays.",
        price=850000.0,
        property_type="Apartment",
        listing_type="Sale",
        bedrooms=3,
        bathrooms=3,
        area_sqft=2400.0,
        address="742 Evergreen Terrace, Downtown",
        city="New York",
        state="NY",
        pincode="10001",
        amenities="Infinity Pool, Fitness Center, 2 Car Parking, 24/7 Security, Private Elevator, Concierge",
        seller_id=seller.id,
        status=PropertyStatus.AVAILABLE,
    )
    db.add(prop1)
    db.flush()

    db.add_all([
        PropertyImage(
            property_id=prop1.id,
            image_url="https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=1200&q=80",
            is_primary=True,
        ),
        PropertyImage(
            property_id=prop1.id,
            image_url="https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
            is_primary=False,
        ),
    ])

    prop2 = Property(
        title="Modernist Architectural Villa with Private Garden",
        description="Striking modern villa designed by renowned architects. Expansive glass walls overlooking landscaped gardens and private heated pool. Includes bespoke chef's kitchen, home cinema, and high-efficiency geothermal heating.",
        price=1450000.0,
        property_type="Villa",
        listing_type="Sale",
        bedrooms=5,
        bathrooms=5,
        area_sqft=4800.0,
        address="12 Ocean Breeze Way",
        city="Miami",
        state="FL",
        pincode="33101",
        amenities="Private Heated Pool, Home Theater, Smart Security, Double Garage, Garden, Solar Panels",
        seller_id=seller.id,
        status=PropertyStatus.AVAILABLE,
    )
    db.add(prop2)
    db.flush()

    db.add_all([
        PropertyImage(
            property_id=prop2.id,
            image_url="https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1200&q=80",
            is_primary=True,
        ),
        PropertyImage(
            property_id=prop2.id,
            image_url="https://images.unsplash.com/photo-1600566753376-12c8ab7fb75b?auto=format&fit=crop&w=1200&q=80",
            is_primary=False,
        ),
    ])

    prop3 = Property(
        title="Cozy Contemporary 2BHK Condo in Tech Corridor",
        description="Ideal for professionals or young families. Low-maintenance condo with open-plan layout, quartz countertops, high-speed fiber internet infrastructure, and EV charging station on premises.",
        price=420000.0,
        property_type="Apartment",
        listing_type="Sale",
        bedrooms=2,
        bathrooms=2,
        area_sqft=1150.0,
        address="304 Silicon Boulevard",
        city="Austin",
        state="TX",
        pincode="78701",
        amenities="EV Charging, Co-Working Lounge, Dog Park, Rooftop Deck, Gym",
        seller_id=seller.id,
        status=PropertyStatus.AVAILABLE,
    )
    db.add(prop3)
    db.flush()

    db.add(PropertyImage(
        property_id=prop3.id,
        image_url="https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
        is_primary=True,
    ))

    sample_deal = DealMeetingRequest(
        property_id=prop1.id,
        buyer_id=buyer.id,
        seller_id=seller.id,
        buyer_offered_price=840000.0,
        buyer_message="We love the skyline views and would like to conduct an online meeting to finalize purchase terms.",
        buyer_agreed_1pct_fee=True,
        seller_agreed_1pct_fee=True,
        status=DealStatus.PENDING_REVIEW,
    )
    db.add(sample_deal)

    db.add(Notification(
        user_id=None,
        is_for_admin=True,
        title=f"New Deal Alert: {prop1.title}",
        message=f"Buyer Emily Davis requested a deal meeting for {prop1.title} (Offer: $840,000.00). 1% commission acknowledged.",
        link_url="/admin",
    ))

    db.commit()
