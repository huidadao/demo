"""Authentication service for JWT and password handling."""

from datetime import datetime, timedelta
from typing import Optional
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
