"""Authentication service for JWT and password handling."""

from datetime import datetime, timedelta
from typing import Optional, List
from sqlmodel import select
import bcrypt
import jwt

from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, TokenResponse

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


def create_access_token(user_id: int, email: str) -> str:
    """
    Create a JWT access token.

    Args:
        user_id: User's ID
        email: User's email

    Returns:
        JWT token string
    """
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "email": email,
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

    if not verify_password(login_data.password, user.password_hash):
        return None

    return user


def create_token_response(user: User) -> TokenResponse:
    """
    Create token response for authenticated user.

    Args:
        user: Authenticated User object

    Returns:
        TokenResponse with access token
    """
    access_token = create_access_token(user.id, user.email)
    return TokenResponse(access_token=access_token, token_type="bearer")


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
