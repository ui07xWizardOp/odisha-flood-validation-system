import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database Connection URL
# Fallback to SQLite if PostgreSQL is not configured (for local development)
_db_url = os.getenv("DATABASE_URL", "")

# Check if this is a placeholder or invalid URL
if not _db_url or "YOUR_SECURE_PASSWORD_HERE" in _db_url:
    # Use SQLite for local development
    DATABASE_URL = "sqlite:///./flood_validation.db"
    print("[INFO] Using SQLite database for local development")
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    DATABASE_URL = _db_url
    engine = create_engine(DATABASE_URL)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()

def get_db():
    """
    Dependency to get a database session.
    Yields session and closes it after request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
