"""
Authentication API Router

This module provides authentication endpoints for the CoachIQ system including:
- Login with username/password (single-user mode)
- Magic link authentication (multi-user mode)
- User profile endpoints
- Token validation and refresh

The router adapts to the configured authentication mode automatically.
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

from backend.core.dependencies import get_auth_manager, get_notification_manager
from backend.services.auth_manager import (
    AuthenticationError,
    AuthManager,
    AuthMode,
    InvalidTokenError,
)
from backend.services.user_invitation_service import (
    UserInvitationRequest,
    UserInvitationResponse,
    UserInvitationService,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


# Pydantic models for request/response
class Token(BaseModel):
    """JWT token response model."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """JWT token payload data."""

    user_id: str | None = None
    username: str | None = None
    email: str | None = None
    role: str | None = None
    mode: str | None = None


class UserInfo(BaseModel):
    """User information response model."""

    user_id: str
    username: str | None = None
    email: str | None = None
    role: str = "user"
    mode: str
    authenticated: bool = True


class MagicLinkRequest(BaseModel):
    """Magic link request model."""

    email: EmailStr
    redirect_url: str | None = None


class MagicLinkResponse(BaseModel):
    """Magic link response model."""

    message: str
    email: str
    expires_in_minutes: int


class AuthStatus(BaseModel):
    """Authentication status response model."""

    enabled: bool
    mode: str
    jwt_available: bool
    magic_links_enabled: bool
    oauth_enabled: bool


# Dependency functions
async def get_user_invitation_service(
    auth_manager: Annotated[AuthManager, Depends(get_auth_manager)],
    notification_manager: Annotated[Any, Depends(get_notification_manager)],
) -> UserInvitationService:
    """
    Get user invitation service instance.

    Args:
        auth_manager: Authentication manager instance
        notification_manager: Notification manager instance

    Returns:
        UserInvitationService: User invitation service instance
    """
    return UserInvitationService(auth_manager, notification_manager)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_manager: Annotated[AuthManager, Depends(get_auth_manager)],
) -> UserInfo:
    """
    Get current authenticated user from JWT token.

    Args:
        token: JWT token from Authorization header
        auth_manager: Authentication manager instance

    Returns:
        UserInfo: Current user information

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # In no-auth mode, return default admin user
    if auth_manager.auth_mode == AuthMode.NONE:
        return UserInfo(
            user_id="admin",
            username="admin",
            email="admin@localhost",
            role="admin",
            mode="none",
            authenticated=True,
        )

    if not token:
        raise credentials_exception

    try:
        payload = auth_manager.validate_token(token)
        user_id = payload.get("sub")
        username = payload.get("username", "")
        email = payload.get("email", "")
        role = payload.get("role", "user")
        mode = payload.get("mode", auth_manager.auth_mode.value)

        if not user_id:
            raise credentials_exception

        return UserInfo(
            user_id=user_id,
            username=username,
            email=email,
            role=role,
            mode=mode,
            authenticated=True,
        )

    except InvalidTokenError:
        raise credentials_exception from None


async def get_current_admin_user(
    current_user: Annotated[UserInfo, Depends(get_current_user)],
) -> UserInfo:
    """
    Get current user and verify admin privileges.

    Args:
        current_user: Current authenticated user

    Returns:
        UserInfo: Current admin user information

    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required"
        )
    return current_user


# Authentication endpoints
@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_manager: Annotated[AuthManager, Depends(get_auth_manager)],
) -> Token:
    """
    Authenticate user with username and password (single-user mode).

    Args:
        form_data: OAuth2 form data with username and password
        auth_manager: Authentication manager instance

    Returns:
        Token: JWT access token and metadata

    Raises:
        HTTPException: If authentication fails or not in single-user mode
    """
    if auth_manager.auth_mode == AuthMode.NONE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Authentication is disabled"
        )

    if auth_manager.auth_mode != AuthMode.SINGLE_USER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username/password login not available in this mode",
        )

    try:
        # Authenticate admin user
        token = await auth_manager.authenticate_admin(form_data.username, form_data.password)

        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        logger.info(f"Successful login for user: {form_data.username}")

        return Token(
            access_token=token,
            token_type="bearer",
            expires_in=auth_manager.settings.jwt_expire_minutes * 60,
        )

    except AuthenticationError as e:
        logger.warning(f"Authentication failed for user {form_data.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


@router.post("/magic-link", response_model=MagicLinkResponse)
async def send_magic_link(
    request: MagicLinkRequest, auth_manager: Annotated[AuthManager, Depends(get_auth_manager)]
) -> MagicLinkResponse:
    """
    Send magic link for passwordless authentication (multi-user mode).

    Args:
        request: Magic link request with email and optional redirect URL
        auth_manager: Authentication manager instance

    Returns:
        MagicLinkResponse: Confirmation message and metadata

    Raises:
        HTTPException: If magic links are not enabled or email sending fails
    """
    if auth_manager.auth_mode == AuthMode.NONE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Authentication is disabled"
        )

    if not auth_manager.settings.enable_magic_links:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Magic links are not enabled"
        )

    try:
        success = await auth_manager.send_magic_link_email(
            email=request.email,
            expires_minutes=auth_manager.settings.magic_link_expire_minutes,
            redirect_url=request.redirect_url,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send magic link email",
            )

        logger.info(f"Magic link sent to: {request.email}")

        return MagicLinkResponse(
            message="Magic link sent successfully",
            email=request.email,
            expires_in_minutes=auth_manager.settings.magic_link_expire_minutes,
        )

    except Exception as e:
        logger.error(f"Failed to send magic link to {request.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send magic link"
        ) from e


@router.get("/magic", response_model=Token)
async def verify_magic_link(
    token: str, auth_manager: Annotated[AuthManager, Depends(get_auth_manager)]
) -> Token:
    """
    Verify magic link token and return access token.

    Args:
        token: Magic link token from URL parameter
        auth_manager: Authentication manager instance

    Returns:
        Token: JWT access token for authenticated user

    Raises:
        HTTPException: If magic link token is invalid or expired
    """
    if auth_manager.auth_mode == AuthMode.NONE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Authentication is disabled"
        )

    try:
        user_info = await auth_manager.validate_magic_link(token)

        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired magic link"
            )

        # Generate new access token for the user
        access_token = auth_manager.generate_token(
            user_id=user_info["user_id"],
            username=user_info["email"],
            additional_claims={
                "email": user_info["email"],
                "role": "user",  # Default role for magic link users
                "mode": "multi-user",
            },
        )

        logger.info(f"Successful magic link authentication for: {user_info['email']}")

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=auth_manager.settings.jwt_expire_minutes * 60,
        )

    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired magic link"
        ) from None
    except Exception as e:
        logger.error(f"Magic link verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Magic link verification failed",
        ) from e


@router.get("/me", response_model=UserInfo)
async def get_user_profile(
    current_user: Annotated[UserInfo, Depends(get_current_user)],
) -> UserInfo:
    """
    Get current user profile information.

    Args:
        current_user: Current authenticated user

    Returns:
        UserInfo: Current user profile data
    """
    return current_user


@router.get("/status", response_model=AuthStatus)
async def get_auth_status(
    auth_manager: Annotated[AuthManager, Depends(get_auth_manager)],
) -> AuthStatus:
    """
    Get authentication system status and configuration.

    Args:
        auth_manager: Authentication manager instance

    Returns:
        AuthStatus: Authentication system status
    """
    return AuthStatus(
        enabled=auth_manager.settings.enabled,
        mode=auth_manager.auth_mode.value,
        jwt_available=bool(auth_manager.settings.secret_key),
        magic_links_enabled=auth_manager.settings.enable_magic_links,
        oauth_enabled=auth_manager.settings.enable_oauth,
    )


@router.post("/logout")
async def logout(current_user: Annotated[UserInfo, Depends(get_current_user)]) -> dict[str, str]:
    """
    Logout current user (placeholder for future session management).

    Args:
        current_user: Current authenticated user

    Returns:
        dict[str, str]: Logout confirmation message

    Note:
        In the current implementation, JWT tokens cannot be invalidated
        server-side. This endpoint is provided for client-side token cleanup
        and future session management features.
    """
    logger.info(f"User logout: {current_user.user_id}")

    return {
        "message": "Logged out successfully",
        "detail": "Please remove the token from your client",
    }


# User invitation endpoints
@router.post("/invitation/send", response_model=UserInvitationResponse)
async def send_user_invitation(
    request: UserInvitationRequest,
    current_admin: Annotated[UserInfo, Depends(get_current_admin_user)],
    invitation_service: Annotated[UserInvitationService, Depends(get_user_invitation_service)],
) -> UserInvitationResponse:
    """
    Send a user invitation (admin only).

    Args:
        request: Invitation request details
        current_admin: Current admin user
        invitation_service: User invitation service instance

    Returns:
        UserInvitationResponse: Created invitation details

    Raises:
        HTTPException: If invitation creation fails
    """
    try:
        invitation = await invitation_service.create_invitation(
            email=request.email,
            invited_by_admin=current_admin.user_id,
            role=request.role,
            message=request.message,
        )

        logger.info(f"Admin {current_admin.user_id} sent invitation to {request.email}")
        return invitation

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Failed to create invitation for {request.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create invitation"
        ) from e


@router.get("/invitation/accept", response_model=Token)
async def accept_user_invitation(
    token: str,
    invitation_service: Annotated[UserInvitationService, Depends(get_user_invitation_service)],
) -> Token:
    """
    Accept a user invitation and get authentication token.

    Args:
        token: Invitation token from URL parameter
        invitation_service: User invitation service instance

    Returns:
        Token: JWT access token for the new user

    Raises:
        HTTPException: If invitation token is invalid or expired
    """
    try:
        magic_token = await invitation_service.accept_invitation(token)

        if not magic_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired invitation"
            )

        # Validate the magic token and get user info
        from backend.core.dependencies import get_auth_manager

        auth_manager = get_auth_manager()
        user_info = await auth_manager.validate_magic_link(magic_token)

        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to authenticate after invitation acceptance",
            )

        # Generate final access token
        access_token = auth_manager.generate_token(
            user_id=user_info["user_id"],
            username=user_info["email"],
            additional_claims={
                "email": user_info["email"],
                "role": "user",  # Default role for invited users
                "mode": "multi-user",
            },
        )

        logger.info(f"User invitation accepted and authenticated: {user_info['email']}")

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=auth_manager.settings.jwt_expire_minutes * 60,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to accept invitation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to accept invitation"
        ) from e


# Admin endpoints
@router.get("/admin/users", dependencies=[Depends(get_current_admin_user)])
async def list_users() -> dict[str, Any]:
    """
    List all users (admin only).

    Returns:
        dict[str, Any]: List of users (placeholder for future implementation)

    Note:
        This endpoint is a placeholder for future multi-user functionality
        when database-backed user management is implemented.
    """
    return {"message": "User management not yet implemented", "users": [], "total": 0}


@router.get("/admin/invitations", dependencies=[Depends(get_current_admin_user)])
async def list_invitations(
    invitation_service: Annotated[UserInvitationService, Depends(get_user_invitation_service)],
    include_expired: bool = False,
    include_used: bool = False,
) -> dict[str, Any]:
    """
    List user invitations (admin only).

    Args:
        include_expired: Include expired invitations
        include_used: Include used invitations
        invitation_service: User invitation service instance

    Returns:
        dict[str, Any]: List of invitations and statistics
    """
    invitations = await invitation_service.list_invitations(include_expired, include_used)
    stats = await invitation_service.get_invitation_stats()

    return {
        "invitations": [inv.model_dump() for inv in invitations],
        "total": len(invitations),
        "stats": stats,
    }


@router.delete("/admin/invitations/{invitation_id}", dependencies=[Depends(get_current_admin_user)])
async def revoke_invitation(
    invitation_id: str,
    invitation_service: Annotated[UserInvitationService, Depends(get_user_invitation_service)],
) -> dict[str, str]:
    """
    Revoke a user invitation (admin only).

    Args:
        invitation_id: ID of invitation to revoke
        invitation_service: User invitation service instance

    Returns:
        dict[str, str]: Revocation confirmation

    Raises:
        HTTPException: If invitation not found
    """
    success = await invitation_service.revoke_invitation(invitation_id)

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")

    return {"message": "Invitation revoked successfully"}


@router.get("/admin/stats", dependencies=[Depends(get_current_admin_user)])
async def get_auth_stats(
    auth_manager: Annotated[AuthManager, Depends(get_auth_manager)],
    invitation_service: Annotated[UserInvitationService, Depends(get_user_invitation_service)],
) -> dict[str, Any]:
    """
    Get detailed authentication statistics (admin only).

    Args:
        auth_manager: Authentication manager instance
        invitation_service: User invitation service instance

    Returns:
        dict[str, Any]: Detailed authentication statistics
    """
    auth_stats = await auth_manager.get_stats()
    invitation_stats = await invitation_service.get_invitation_stats()

    return {
        "authentication": auth_stats,
        "invitations": invitation_stats,
        "endpoints": {
            "login_enabled": auth_manager.auth_mode == AuthMode.SINGLE_USER,
            "magic_links_enabled": auth_manager.settings.enable_magic_links,
            "oauth_enabled": auth_manager.settings.enable_oauth,
            "invitations_enabled": auth_manager.auth_mode == AuthMode.MULTI_USER,
        },
    }
