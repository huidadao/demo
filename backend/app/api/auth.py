"""Authentication API endpoints."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession
import aiosmtplib

from app.database import get_session
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    MessageResponse,
    UserUpdate,
    ForgotPasswordRequest,
    ChangePasswordRequest,
    RegisterResponse,
    VerifyEmailRequest,
    ResendVerificationRequest,
)
from app.services import auth_service
from app.dependencies.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_session),
):
    """
    Register a new user account and send verification email.

    Args:
        user_data: User registration data
        session: Database session

    Returns:
        Registration response with verification options

    Raises:
        HTTPException: If email already registered or SMTP error
    """
    try:
        result = await auth_service.register_user(session, user_data)
        return RegisterResponse(
            message="Account created. Please verify your email.",
            email=result["user"].email,
            verification_options=result["verification_options"],
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except aiosmtplib.SMTPAuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}",
        )


@router.post("/login")
async def login(
    login_data: UserLogin,
    session: AsyncSession = Depends(get_session),
):
    """
    Authenticate user and return JWT token.
    If user is not verified, resend verification email.

    Args:
        login_data: User login credentials
        session: Database session

    Returns:
        Access token or verification required response

    Raises:
        HTTPException: If credentials are invalid
    """
    user = await auth_service.authenticate_user(session, login_data)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is verified
    if not user.is_verified:
        try:
            verification_data = await auth_service.resend_verification(session, user.email)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": "Email not verified. A new verification code has been sent to your email.",
                    "email": user.email,
                    "verification_options": verification_data["options"],
                },
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to resend verification: {str(e)}",
            )

    # Update last_seen_at on successful login
    user.last_seen_at = datetime.utcnow()
    session.add(user)
    session.commit()
    session.refresh(user)

    return auth_service.create_token_response(user)


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    data: VerifyEmailRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Verify user's email with the provided code.

    Args:
        data: Verification request with email and code
        session: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If verification fails
    """
    try:
        await auth_service.verify_email(session, data.email, data.code)
        return MessageResponse(message="Email verified successfully. You can now log in.")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/resend-verification")
async def resend_verification(
    data: ResendVerificationRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Resend verification email to user.

    Args:
        data: Resend verification request with email
        session: Database session

    Returns:
        Verification options for frontend display

    Raises:
        HTTPException: If user not found or already verified
    """
    try:
        verification_data = await auth_service.resend_verification(session, data.email)
        return {
            "message": "Verification code sent to your email.",
            "email": data.email,
            "verification_options": verification_data["options"],
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except aiosmtplib.SMTPAuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}",
        )


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    data: ForgotPasswordRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Send temporary password to user's email.

    Args:
        data: Forgot password request with email
        session: Database session

    Returns:
        Success message if email exists

    Raises:
        HTTPException: 404 if email not found, 503 if SMTP misconfigured/auth failed, 500 otherwise
    """
    try:
        await auth_service.forgot_password(session, data.email)
        return MessageResponse(message="Temporary password sent to your email")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except aiosmtplib.SMTPAuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}",
        )


@router.put("/change-password", response_model=MessageResponse)
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Change user password.

    Args:
        data: Change password request
        current_user: Authenticated user
        session: Database session

    Returns:
        Success message
    """
    try:
        await auth_service.change_password(
            session,
            current_user.id,
            data.current_password,
            data.new_password,
        )
        return MessageResponse(message="Password changed successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_endpoint(
    current_user: User = Depends(get_current_user),
):
    """
    Get current authenticated user.

    Requires valid JWT token in Authorization header.

    Args:
        current_user: User from JWT validation (injected by dependency)

    Returns:
        Current user information
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Update current user profile.

    Requires valid JWT token in Authorization header.

    Args:
        user_update: Update data
        current_user: User from JWT validation (injected by dependency)
        session: Database session

    Returns:
        Updated user information
    """
    try:
        updated_user = await auth_service.update_user(
            session,
            current_user.id,
            email=user_update.email,
        )
        return updated_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/stats")
async def get_stats(
    session: AsyncSession = Depends(get_session),
):
    """
    Get dashboard statistics.

    Args:
        session: Database session

    Returns:
        Dashboard statistics including user counts and active users
    """
    return await run_in_threadpool(auth_service.get_dashboard_stats, session)
