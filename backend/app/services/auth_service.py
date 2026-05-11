"""Authentication service for JWT and password handling."""

import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, List
from sqlmodel import select
import bcrypt
import jwt

from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, TokenResponse
from app.services.email_service import EmailService

# JWT Configuration
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored hashed password

    Returns:
        True if password matches, False otherwise
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def create_access_token(user_id: int, email: str, must_change_password: bool = False) -> str:
    """
    Create a JWT access token.

    Args:
        user_id: User's ID
        email: User's email
        must_change_password: Whether user must change password on next login

    Returns:
        JWT token string
    """
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "email": email,
        "must_change_password": must_change_password,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


async def register_user(session, user_data: UserCreate) -> User:
    """
    Register a new user.

    Args:
        session: Database session
        user_data: User registration data

    Returns:
        Created User object

    Raises:
        ValueError: If email already exists
    """
    # Check if user already exists
    statement = select(User).where(User.email == user_data.email)
    existing_user = session.exec(statement).first()

    if existing_user:
        raise ValueError("Email already registered")

    # Hash password and create user
    hashed_password = hash_password(user_data.password)
    db_user = User(
        email=user_data.email,
        password_hash=hashed_password,
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return db_user


async def authenticate_user(session, login_data: UserLogin) -> Optional[User]:
    """
    Authenticate a user by email and password.
    Also accepts valid temporary passwords.

    Args:
        session: Database session
        login_data: User login data

    Returns:
        User object if authentication successful, None otherwise
    """
    statement = select(User).where(User.email == login_data.email)
    user = session.exec(statement).first()

    if not user:
        return None

    # Check regular password
    if verify_password(login_data.password, user.password_hash):
        return user

    # Check temporary password if exists and not expired
    if user.temp_password_hash and user.temp_password_expires_at:
        if datetime.utcnow() <= user.temp_password_expires_at:
            if verify_password(login_data.password, user.temp_password_hash):
                return user


def create_token_response(user: User) -> TokenResponse:
    """
    Create token response for authenticated user.

    Args:
        user: Authenticated User object

    Returns:
        TokenResponse with access token and must_change_password flag
    """
    access_token = create_access_token(
        user.id, user.email, must_change_password=user.must_change_password
    )
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        must_change_password=user.must_change_password,
    )


def generate_temp_password(length: int = 12) -> str:
    """Generate a random temporary password."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


async def forgot_password(session, email: str) -> None:
    """
    Generate a temporary password and send it via email.

    Args:
        session: Database session
        email: User's email address

    Raises:
        ValueError: If user not found
    """
    statement = select(User).where(User.email == email)
    user = session.exec(statement).first()

    if not user:
        raise ValueError("User not found")

    temp_password = generate_temp_password()
    temp_hash = hash_password(temp_password)

    user.temp_password_hash = temp_hash
    user.temp_password_expires_at = datetime.utcnow() + timedelta(hours=1)
    user.must_change_password = True
    user.updated_at = datetime.utcnow()

    session.add(user)
    session.commit()
    session.refresh(user)

    # Send email (async)
    email_service = EmailService()
    await email_service.send_temp_password(email, temp_password)


async def change_password(
    session, user_id: int, current_password: str, new_password: str
) -> User:
    """
    Change user password after verifying current password.

    Args:
        session: Database session
        user_id: User's ID
        current_password: Current or temporary password
        new_password: New password to set

    Returns:
        Updated User object

    Raises:
        ValueError: If user not found or current password is invalid
    """
    statement = select(User).where(User.id == user_id)
    user = session.exec(statement).first()

    if not user:
        raise ValueError("User not found")

    # Verify current password (regular or temporary)
    valid = verify_password(current_password, user.password_hash)
    if not valid and user.temp_password_hash:
        if (
            user.temp_password_expires_at
            and datetime.utcnow() <= user.temp_password_expires_at
        ):
            valid = verify_password(current_password, user.temp_password_hash)

    if not valid:
        raise ValueError("Current password is incorrect")

    # Update password
    user.password_hash = hash_password(new_password)
    user.temp_password_hash = None
    user.temp_password_expires_at = None
    user.must_change_password = False
    user.updated_at = datetime.utcnow()

    session.add(user)
    session.commit()
    session.refresh(user)

    return user


async def update_user(session, user_id: int, email: Optional[str] = None) -> User:
    """
    Update user profile.

    Args:
        session: Database session
        user_id: User's ID to update
        email: New email (optional)

    Returns:
        Updated User object

    Raises:
        ValueError: If email already exists
    """
    statement = select(User).where(User.id == user_id)
    user = session.exec(statement).first()

    if not user:
        raise ValueError("User not found")

    # Check if email is being changed and if it's already taken
    if email and email != user.email:
        check_statement = select(User).where(User.email == email)
        existing_user = session.exec(check_statement).first()
        if existing_user:
            raise ValueError("Email already in use")
        user.email = email

    user.updated_at = datetime.utcnow()
    session.add(user)
    session.commit()
    session.refresh(user)

    return user


def get_dashboard_stats(session) -> dict:
    """
    Get dashboard statistics for users.

    Args:
        session: Database session

    Returns:
        Dictionary with total_users, today_signups, active_users, and users list
    """
    # Total users count
    total_statement = select(User)
    all_users = session.exec(total_statement).all()
    total_users = len(all_users)

    # Today's signups
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_signups = sum(1 for u in all_users if u.created_at and u.created_at >= today)

    # Active users (seen in last 30 minutes)
    active_threshold = datetime.utcnow() - timedelta(minutes=30)
    active_users_list: List[User] = [
        u for u in all_users
        if u.last_seen_at and u.last_seen_at >= active_threshold
    ]
    active_users = len(active_users_list)

    # Prepare user status list
    users_status = []
    now = datetime.utcnow()
    for u in all_users:
        if u.last_seen_at and u.last_seen_at >= active_threshold:
            status = "online"
        elif u.last_seen_at and u.last_seen_at >= now - timedelta(minutes=60):
            status = "away"
        else:
            status = "offline"

        users_status.append({
            "id": u.id,
            "email": u.email,
            "status": status,
            "last_seen": u.last_seen_at.isoformat() if u.last_seen_at else None,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        })

    return {
        "total_users": total_users,
        "today_signups": today_signups,
        "active_users": active_users,
        "users": users_status,
    }
