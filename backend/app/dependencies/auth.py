"""JWT token dependency for protected routes."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import select

from datetime import datetime

from app.models.user import User
from app.database import get_session
from app.services.auth_service import decode_token
from typing import Optional

security = HTTPBearer()


class TokenData:
    """Token data extracted from JWT."""

    def __init__(self, user_id: int, email: str):
        self.user_id = user_id
        self.email = email


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session=Depends(get_session),
) -> User:
    """
    Validate JWT token and return current user.

    Args:
        credentials: Bearer token from Authorization header
        session: Database session

    Returns:
        User object from database

    Raises:
        HTTPException: If token is invalid or expired
    """
    # Decode token
    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user info from token
    user_id = int(payload.get("sub"))
    email = payload.get("email")

    if not user_id or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    statement = select(User).where(User.id == user_id)
    user = session.exec(statement).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last seen timestamp
    user.last_seen_at = datetime.utcnow()
    session.add(user)
    session.commit()

    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    session=Depends(get_session),
) -> Optional[User]:
    """
    Optional JWT validation - returns None if no valid token.

    Args:
        credentials: Optional Bearer token
        session: Database session

    Returns:
        User object if valid token, None otherwise
    """
    if not credentials:
        return None

    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        return None

    user_id = int(payload.get("sub"))
    statement = select(User).where(User.id == user_id)
    user = session.exec(statement).first()

    return user
