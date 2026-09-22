from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

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

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Uploads directory
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include API Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(properties.router, prefix=settings.API_V1_STR)
app.include_router(deals.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)
app.include_router(notifications.router, prefix=settings.API_V1_STR)

# Serve Frontend SPA
@app.get("/", include_in_schema=False)
def serve_frontend():
    index_file = settings.STATIC_DIR / "index.html"
    return FileResponse(index_file)

# Mount Static assets
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")
