"""Authentication routes."""

import logging

from fastapi import APIRouter, HTTPException, Request, Response, status
from slowapi.util import get_remote_address

from app.core.config import get_settings
from app.core.limiter import limiter
from app.models import (
    CsrfResponse,
    LoginRequest,
    LoginResponse,
    LoginUserPublic,
    LogoutResponse,
    MessageResponse,
    SignupRequest,
    SignupResponse,
    UserPublic,
)
from app.core.security import (
    ACCESS_TOKEN_COOKIE,
    REFRESH_TOKEN_COOKIE,
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.utils.csrf import CSRF_COOKIE_NAME, generate_csrf_token
from app.services.user_service import create_user, get_user_by_email

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/csrf", response_model=CsrfResponse)
async def get_csrf_token(response: Response) -> CsrfResponse:
    """
    Issue a CSRF token via double-submit cookie pattern.

    The token is returned in the response body and set as a readable cookie.
    Clients must send the same value in the X-CSRF-Token header on mutating requests.
    """
    settings = get_settings()
    token = generate_csrf_token()
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=token,
        httponly=False,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=3600,
        path="/",
    )
    return CsrfResponse(csrf_token=token)


def _set_auth_cookies(
    response: Response,
    *,
    access_token: str,
    refresh_token: str | None = None,
) -> None:
    """Set httpOnly authentication cookies on the response."""
    settings = get_settings()
    access_max_age = settings.access_token_expire_hours * 3600

    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=access_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=access_max_age,
        path="/",
    )

    if refresh_token:
        refresh_max_age = settings.refresh_token_expire_days * 86400
        response.set_cookie(
            key=REFRESH_TOKEN_COOKIE,
            value=refresh_token,
            httponly=True,
            secure=settings.cookie_secure,
            samesite="lax",
            max_age=refresh_max_age,
            path="/",
        )


def _clear_auth_cookies(response: Response) -> None:
    """Remove authentication cookies from the response."""
    settings = get_settings()
    response.delete_cookie(
        key=ACCESS_TOKEN_COOKIE,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )
    response.delete_cookie(
        key=REFRESH_TOKEN_COOKIE,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


@router.post(
    "/signup",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": MessageResponse, "description": "Signup failed"},
        422: {"description": "Validation error"},
    },
)
@limiter.limit("5/minute")
async def signup(request: Request, payload: SignupRequest, response: Response) -> SignupResponse:
    """
    Register a new user account.

    Validates input, stores a bcrypt-hashed password in Supabase, and issues
    JWT access and refresh tokens in httpOnly cookies.
    """
    email = str(payload.email).lower()

    if get_user_by_email(email):
        logger.warning("Signup rejected for existing email from ip=%s", get_remote_address(request))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Signup failed",
        )

    password_hash = hash_password(payload.password)
    user = create_user(email=email, password_hash=password_hash, full_name=payload.full_name)

    if not user:
        logger.error("Failed to create user for email=%s", email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Signup failed",
        )

    access_token = create_access_token(user_id=str(user["id"]), email=user["email"])
    refresh_token = create_refresh_token(user_id=str(user["id"]))
    _set_auth_cookies(response, access_token=access_token, refresh_token=refresh_token)

    logger.info("Signup successful for user id=%s", user["id"])

    return SignupResponse(
        message="Signup successful",
        user=UserPublic(
            id=str(user["id"]),
            email=user["email"],
            full_name=user["full_name"],
        ),
    )


@router.post(
    "/login",
    response_model=LoginResponse,
    responses={
        401: {"model": MessageResponse, "description": "Invalid credentials"},
        422: {"description": "Validation error"},
    },
)
@limiter.limit("5/minute")
async def login(request: Request, payload: LoginRequest, response: Response) -> LoginResponse:
    """
    Authenticate an existing user.

    Verifies credentials against Supabase and returns access and refresh tokens
    in httpOnly cookies.
    """
    email = str(payload.email).lower()
    client_ip = get_remote_address(request)

    user = get_user_by_email(email)
    if not user or not verify_password(payload.password, user["password_hash"]):
        logger.warning("Failed login attempt for email=%s from ip=%s", email, client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    user_id = str(user["id"])
    access_token = create_access_token(user_id=user_id, email=user["email"])
    refresh_token = create_refresh_token(user_id=user_id)
    _set_auth_cookies(response, access_token=access_token, refresh_token=refresh_token)

    logger.info("Login successful for user id=%s", user_id)

    return LoginResponse(
        message="Login successful",
        user=LoginUserPublic(id=user_id, email=user["email"]),
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(response: Response) -> LogoutResponse:
    """Clear authentication cookies and end the session."""
    _clear_auth_cookies(response)
    return LogoutResponse(message="Logged out")
