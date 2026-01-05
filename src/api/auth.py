"""
JWT Authentication Module for Flood Validation API.

Provides:
- JWT token generation and validation
- Password hashing with bcrypt
- OAuth2 password bearer scheme
"""

from datetime import datetime, timedelta
from typing import Optional
import os

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

# Try to import authentication libraries
try:
    from jose import JWTError, jwt
    JOSE_AVAILABLE = True
except ImportError:
    JOSE_AVAILABLE = False
    print("Warning: python-jose not installed. JWT auth disabled.")

try:
    from passlib.context import CryptContext
    PASSLIB_AVAILABLE = True
except ImportError:
    PASSLIB_AVAILABLE = False
    print("Warning: passlib not installed. Password hashing disabled.")

from pydantic import BaseModel


# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "flood-validation-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS = 7  # 7 days

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

# Password hashing context
if PASSLIB_AVAILABLE:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
else:
    pwd_context = None


# Pydantic models
class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None


class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None


class UserCreate(BaseModel):
    username: str
    email: Optional[str] = None
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    if not PASSLIB_AVAILABLE:
        # Fallback: simple comparison (NOT secure for production)
        return plain_password == hashed_password
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    if not PASSLIB_AVAILABLE:
        # Fallback: return as-is (NOT secure for production)
        return password
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    if not JOSE_AVAILABLE:
        # Fallback: return a simple token
        return f"mock-token-{data.get('sub', 'unknown')}"
    
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token with longer expiry."""
    if not JOSE_AVAILABLE:
        return f"mock-refresh-{data.get('sub', 'unknown')}"
    
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_refresh_token(token: str) -> Optional[TokenData]:
    """Decode and validate a refresh token."""
    if not JOSE_AVAILABLE:
        if token and token.startswith("mock-refresh-"):
            username = token.replace("mock-refresh-", "")
            return TokenData(username=username, user_id=1)
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Verify it's a refresh token
        if payload.get("type") != "refresh":
            return None
        
        user_id: int = payload.get("sub")
        username: str = payload.get("username")
        
        if user_id is None:
            return None
            
        return TokenData(user_id=user_id, username=username)
        
    except JWTError:
        return None


def decode_token(token: str) -> Optional[TokenData]:
    """Decode and validate a JWT token."""
    if not JOSE_AVAILABLE:
        # Fallback: parse mock token
        if token and token.startswith("mock-token-"):
            username = token.replace("mock-token-", "")
            return TokenData(username=username, user_id=1)
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        username: str = payload.get("username")
        
        if user_id is None:
            return None
            
        return TokenData(user_id=user_id, username=username)
        
    except JWTError:
        return None


async def get_current_user_optional(token: Optional[str] = Depends(oauth2_scheme)):
    """
    Get current user from token (optional - allows anonymous access).
    Returns None if no valid token provided.
    """
    if token is None:
        return None
    
    token_data = decode_token(token)
    return token_data


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Get current user from token (required - blocks anonymous access).
    Raises HTTPException if no valid token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if token is None:
        raise credentials_exception
    
    token_data = decode_token(token)
    
    if token_data is None:
        raise credentials_exception
    
    return token_data


def is_auth_available() -> bool:
    """Check if authentication libraries are available."""
    return JOSE_AVAILABLE and PASSLIB_AVAILABLE
