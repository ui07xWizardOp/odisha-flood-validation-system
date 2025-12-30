import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database Connection URL
# Fallback to default if not set (for development)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://flood_admin:flood_secure_password_2024@localhost:5432/flood_validation")

# Create Engine
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
