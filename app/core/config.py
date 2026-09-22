import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load .env if present
load_dotenv(BASE_DIR / ".env")

class Settings:
    PROJECT_NAME: str = "Real Estate Marketplace"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "realestate-super-secret-jwt-key-2026-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database: Supports PostgreSQL via DATABASE_URL or individual POSTGRES_* vars; defaults to SQLite if not provided
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "")

    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    if not DATABASE_URL and POSTGRES_USER and POSTGRES_DB:
        DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    
    if not DATABASE_URL:
        DATABASE_URL = f"sqlite:///{BASE_DIR / 'realestate.db'}"

    # Normalize hosted PostgreSQL URLs (e.g. Render, Heroku, Railway supply "postgres://")
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    # 1% Marketplace Platform Commission Policy
    COMMISSION_PERCENT_SELLER: float = float(os.getenv("COMMISSION_PERCENT_SELLER", "1.0"))
    COMMISSION_PERCENT_BUYER: float = float(os.getenv("COMMISSION_PERCENT_BUYER", "1.0"))
    
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    STATIC_DIR: Path = BASE_DIR / "app" / "static"

settings = Settings()
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.STATIC_DIR.mkdir(parents=True, exist_ok=True)
