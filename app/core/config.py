import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load .env if present
load_dotenv(BASE_DIR / ".env")

# The insecure fallback key is intentionally unusable in production.
_DEV_FALLBACK_SECRET = "realestate-insecure-dev-only-key"

class Settings:
    PROJECT_NAME: str = "Real Estate Marketplace"
    VERSION: str = "1.1.0"
    API_V1_STR: str = "/api/v1"

    # "development" (demo seeds + permissive defaults) or "production" (strict)
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").strip().lower()

    SECRET_KEY: str = os.getenv("SECRET_KEY", "").strip() or _DEV_FALLBACK_SECRET
    if ENVIRONMENT == "production" and (not os.getenv("SECRET_KEY") or SECRET_KEY == _DEV_FALLBACK_SECRET):
        raise RuntimeError(
            "SECRET_KEY must be set to a strong random value in production. "
            "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
        )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7)))  # 7 days

    # Comma-separated list of allowed browser origins. "*" disables credentials.
    CORS_ORIGINS: list = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]

    # Admin bootstrap account (created on first run / used to reset a weak default)
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@realestate.com").strip().lower()
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "").strip() or secrets.token_urlsafe(14)

    # Upload constraints
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "5"))
    MAX_UPLOAD_FILES: int = int(os.getenv("MAX_UPLOAD_FILES", "10"))

    # Simple in-memory rate limits (requests per window)
    RATE_LIMIT_AUTH: int = int(os.getenv("RATE_LIMIT_AUTH", "10"))        # per window
    RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
    
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

settings = Settings()
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Demo data / quick-login only exist outside production.
settings.DEMO_MODE = settings.ENVIRONMENT != "production"
