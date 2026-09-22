from sqlalchemy.orm import Session
from app.core.database import Base, engine, SessionLocal
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.property import Property, PropertyImage, PropertyStatus
from app.models.deal_meeting import DealMeetingRequest, DealStatus
from app.models.notification import Notification

def init_db():
    # Create all tables
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # Check if users already seeded
        admin = db.query(User).filter(User.email == "admin@realestate.com").first()
        if not admin:
            # 1. Admin
            admin = User(
                full_name="Platform Admin / Broker",
                email="admin@realestate.com",
                phone="+1 (555) 019-2831",
                hashed_password=get_password_hash("admin123"),
                role=UserRole.ADMIN
            )
            db.add(admin)

            # 2. Sample Seller
            seller = User(
                full_name="David Miller (Seller)",
                email="seller@realestate.com",
                phone="+1 (555) 234-5678",
                hashed_password=get_password_hash("seller123"),
                role=UserRole.SELLER
            )
            db.add(seller)

            # 3. Sample Buyer
            buyer = User(
                full_name="Emily Davis (Buyer)",
                email="buyer@realestate.com",
                phone="+1 (555) 876-5432",
                hashed_password=get_password_hash("buyer123"),
                role=UserRole.BUYER
            )
            db.add(buyer)
            db.flush()

            # Seed Sample Properties
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
                status=PropertyStatus.AVAILABLE
            )
            db.add(prop1)
            db.flush()

            img1_1 = PropertyImage(
                property_id=prop1.id,
                image_url="https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=1200&q=80",
                is_primary=True
            )
            img1_2 = PropertyImage(
                property_id=prop1.id,
                image_url="https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
                is_primary=False
            )
            db.add_all([img1_1, img1_2])

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
                status=PropertyStatus.AVAILABLE
            )
            db.add(prop2)
            db.flush()

            img2_1 = PropertyImage(
                property_id=prop2.id,
                image_url="https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1200&q=80",
                is_primary=True
            )
            img2_2 = PropertyImage(
                property_id=prop2.id,
                image_url="https://images.unsplash.com/photo-1600566753376-12c8ab7fb75b?auto=format&fit=crop&w=1200&q=80",
                is_primary=False
            )
            db.add_all([img2_1, img2_2])

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
                status=PropertyStatus.AVAILABLE
            )
            db.add(prop3)
            db.flush()

            img3_1 = PropertyImage(
                property_id=prop3.id,
                image_url="https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
                is_primary=True
            )
            db.add(img3_1)

            # Sample Initial Deal Request & Notification
            sample_deal = DealMeetingRequest(
                property_id=prop1.id,
                buyer_id=buyer.id,
                seller_id=seller.id,
                buyer_offered_price=840000.0,
                buyer_message="We love the skyline views and would like to conduct an online meeting to finalize purchase terms.",
                buyer_agreed_1pct_fee=True,
                seller_agreed_1pct_fee=True,
                status=DealStatus.PENDING_REVIEW
            )
            db.add(sample_deal)

            # Admin alert notification
            db.add(Notification(
                user_id=None,
                is_for_admin=True,
                title=f"New Deal Alert: {prop1.title}",
                message=f"Buyer Emily Davis requested a deal meeting for {prop1.title} (Offer: $840,000.00). 1% commission acknowledged.",
                link_url=f"/admin"
            ))

            db.commit()
    finally:
        db.close()
