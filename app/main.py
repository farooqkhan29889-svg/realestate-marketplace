from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.init_db import init_db
from app.routers import auth, properties, deals, admin, notifications

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables & seed demo data on startup
    init_db()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Real Estate Marketplace with Free Seller Listings, Buyer Interest/Meeting Alerts, and 1% Commission Deal Facilitation.",
    lifespan=lifespan
)

# CORS setup. Credentials are only allowed for explicit (non-wildcard) origins.
_allow_credentials = "*" not in settings.CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=_allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    return response

# Mount Uploads directory
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include API Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(properties.router, prefix=settings.API_V1_STR)
app.include_router(deals.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)
app.include_router(notifications.router, prefix=settings.API_V1_STR)

@app.get(f"{settings.API_V1_STR}/meta", include_in_schema=False)
def public_meta():
    """Non-sensitive runtime flags the frontend needs (no secrets exposed)."""
    return {
        "demo_mode": settings.DEMO_MODE,
        "commission_percent_seller": settings.COMMISSION_PERCENT_SELLER,
        "commission_percent_buyer": settings.COMMISSION_PERCENT_BUYER,
    }

@app.get("/", include_in_schema=False)
def root():
    """API root. The user-facing app is the Streamlit frontend (separate process)."""
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "api": settings.API_V1_STR,
    }
