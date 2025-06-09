"""
Authentication Manager for CoachIQ

This module provides a centralized authentication service that handles:
- Authentication mode detection (none, single-user, multi-user)
- JWT token generation and validation
- Admin user management
- Session management
- Magic link generation for passwordless authentication
- Integration with notification system for magic links

The AuthManager follows the existing service patterns in the codebase and
integrates with the feature management system.

Example:
    >>> auth_manager = AuthManager(auth_settings, notification_manager)
    >>> admin_token = await auth_manager.authenticate_admin(username, password)
    >>> magic_link = await auth_manager.generate_magic_link("user@example.com")
    >>> user = await auth_manager.validate_token(token)
"""

import logging
import secrets
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

try:
    import jwt
    from passlib.context import CryptContext

    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

from backend.core.config import AuthenticationSettings


class AuthMode(str, Enum):
    """Authentication modes supported by the system."""

    NONE = "none"  # No authentication required
    SINGLE_USER = "single"  # Single admin user with username/password
    MULTI_USER = "multi"  # Multiple users with magic links and OAuth


class AuthenticationError(Exception):
    """Base exception for authentication errors."""

    pass


class InvalidTokenError(AuthenticationError):
    """Raised when a token is invalid or expired."""

    pass


class UserNotFoundError(AuthenticationError):
    """Raised when a user cannot be found."""

    pass


class AuthManager:
    """
    Centralized authentication manager for CoachIQ.

    Provides authentication services including JWT token management,
    admin user authentication, magic link generation, and mode detection.
    """

    def __init__(
        self,
        auth_settings: AuthenticationSettings,
        notification_manager: Any | None = None,
        **kwargs,
    ):
        """
        Initialize the authentication manager.

        Args:
            auth_settings: Authentication configuration settings
            notification_manager: NotificationManager instance for magic links
            **kwargs: Additional keyword arguments (unused)
        """
        self.settings = auth_settings
        self.notification_manager = notification_manager
        self.logger = logging.getLogger(__name__)

        # Initialize password hashing context
        if JWT_AVAILABLE:
            self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        else:
            self.pwd_context = None
            self.logger.warning("JWT dependencies not available - authentication will be limited")

        # Determine authentication mode
        self.auth_mode = self._detect_auth_mode()
        self.logger.info(f"Authentication mode detected: {self.auth_mode}")

        # Initialize admin credentials if needed
        self._admin_credentials = {}
        if self.auth_mode == AuthMode.SINGLE_USER:
            self._initialize_single_user_admin()

    async def startup(self) -> None:
        """Initialize the authentication manager on startup."""
        self.logger.info("Authentication manager started")

        if self.auth_mode == AuthMode.NONE:
            self.logger.warning("Authentication is DISABLED - all requests will be allowed")
        elif self.auth_mode == AuthMode.SINGLE_USER:
            self.logger.info("Single-user authentication mode enabled")
            if self.settings.admin_username and self.settings.admin_password:
                self.logger.info("Admin credentials configured via environment variables")
            else:
                self.logger.warning("Admin credentials auto-generated - check logs for details")
        elif self.auth_mode == AuthMode.MULTI_USER:
            self.logger.info("Multi-user authentication mode enabled")
            if self.settings.admin_email:
                self.logger.info(f"Admin email configured: {self.settings.admin_email}")
            else:
                self.logger.warning("No admin email configured - will need to be set manually")

    async def shutdown(self) -> None:
        """Cleanup authentication manager on shutdown."""
        self.logger.info("Authentication manager stopped")

    def _detect_auth_mode(self) -> AuthMode:
        """
        Detect the authentication mode based on configuration.

        Returns:
            AuthMode: The detected authentication mode
        """
        # Check if authentication is explicitly disabled
        if not self.settings.enabled:
            return AuthMode.NONE

        # Check for multi-user indicators
        if (
            self.settings.enable_oauth
            or self.settings.enable_magic_links
            or self.settings.admin_email
        ):
            return AuthMode.MULTI_USER

        # Check for single-user indicators
        if self.settings.admin_username or self.settings.admin_password:
            return AuthMode.SINGLE_USER

        # Default to no authentication if nothing is configured
        return AuthMode.NONE

    def _initialize_single_user_admin(self) -> None:
        """Initialize admin credentials for single-user mode."""
        username = self.settings.admin_username or "admin"
        password = self.settings.admin_password

        if not password:
            # Generate a random password
            password = secrets.token_urlsafe(16)
            self.logger.critical(
                f"Auto-generated admin credentials - Username: {username}, Password: {password}"
            )
            self.logger.critical(
                "IMPORTANT: Save these credentials immediately! They will not be displayed again."
            )

        if self.pwd_context:
            password_hash = self.pwd_context.hash(password)
            self._admin_credentials = {
                "username": username,
                "password_hash": password_hash,
                "created_at": datetime.now(UTC),
            }
        else:
            # Fallback for when dependencies aren't available
            self._admin_credentials = {
                "username": username,
                "password": password,  # Store plaintext as fallback
                "created_at": datetime.now(UTC),
            }

    def generate_token(
        self,
        user_id: str,
        username: str = "",
        expires_delta: timedelta | None = None,
        additional_claims: dict[str, Any] | None = None,
    ) -> str:
        """
        Generate a JWT token for a user.

        Args:
            user_id: Unique identifier for the user
            username: Username for the user (optional)
            expires_delta: Token expiration time (defaults to configured value)
            additional_claims: Additional claims to include in the token

        Returns:
            str: The encoded JWT token

        Raises:
            AuthenticationError: If JWT is not available
        """
        if not JWT_AVAILABLE or not self.settings.secret_key:
            raise AuthenticationError("JWT token generation not available")

        if expires_delta is None:
            expires_delta = timedelta(minutes=self.settings.jwt_expire_minutes)

        expire = datetime.now(UTC) + expires_delta

        to_encode = {
            "sub": str(user_id),
            "username": username,
            "exp": expire,
            "iat": datetime.now(UTC),
            "iss": "coachiq",
            "aud": "coachiq-api",
        }

        if additional_claims:
            to_encode.update(additional_claims)

        try:
            encoded_jwt = jwt.encode(
                to_encode, self.settings.secret_key, algorithm=self.settings.jwt_algorithm
            )
            return encoded_jwt
        except Exception as e:
            self.logger.error(f"Failed to generate JWT token: {e}")
            raise AuthenticationError("Token generation failed") from e

    def validate_token(self, token: str) -> dict[str, Any]:
        """
        Validate and decode a JWT token.

        Args:
            token: The JWT token to validate

        Returns:
            Dict[str, Any]: The decoded token payload

        Raises:
            InvalidTokenError: If the token is invalid or expired
        """
        if not JWT_AVAILABLE or not self.settings.secret_key:
            raise InvalidTokenError("JWT validation not available")

        try:
            payload = jwt.decode(
                token,
                self.settings.secret_key,
                algorithms=[self.settings.jwt_algorithm],
                audience="coachiq-api",
                issuer="coachiq",
            )
            return payload
        except jwt.ExpiredSignatureError as e:
            raise InvalidTokenError("Token has expired") from e
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError(f"Invalid token: {e}") from e

    async def authenticate_admin(self, username: str, password: str) -> str | None:
        """
        Authenticate admin user in single-user mode.

        Args:
            username: Admin username
            password: Admin password

        Returns:
            Optional[str]: JWT token if authentication successful, None otherwise
        """
        if self.auth_mode != AuthMode.SINGLE_USER:
            self.logger.warning(f"Admin authentication called in {self.auth_mode} mode")
            return None

        if not self._admin_credentials:
            self.logger.error("No admin credentials configured")
            return None

        # Verify username
        if username != self._admin_credentials["username"]:
            self.logger.warning(f"Invalid admin username: {username}")
            return None

        # Verify password
        if self.pwd_context and "password_hash" in self._admin_credentials:
            # Use bcrypt verification
            if not self.pwd_context.verify(password, self._admin_credentials["password_hash"]):
                self.logger.warning("Invalid admin password")
                return None
        elif "password" in self._admin_credentials:
            # Fallback to plaintext comparison
            if password != self._admin_credentials["password"]:
                self.logger.warning("Invalid admin password")
                return None
        else:
            self.logger.error("No password verification method available")
            return None

        # Generate token
        try:
            token = self.generate_token(
                user_id="admin",
                username=username,
                additional_claims={"role": "admin", "mode": "single-user"},
            )
            self.logger.info(f"Admin user authenticated: {username}")
            return token
        except AuthenticationError as e:
            self.logger.error(f"Failed to generate admin token: {e}")
            return None

    async def generate_magic_link(
        self, email: str, expires_minutes: int = 15, redirect_url: str | None = None
    ) -> str | None:
        """
        Generate a magic link for passwordless authentication.

        Args:
            email: Email address for the magic link
            expires_minutes: Link expiration time in minutes
            redirect_url: URL to redirect to after authentication

        Returns:
            Optional[str]: The magic link URL if successful
        """
        if self.auth_mode == AuthMode.NONE:
            self.logger.warning("Magic link requested but authentication is disabled")
            return None

        try:
            # Generate a secure token
            expires_delta = timedelta(minutes=expires_minutes)
            token = self.generate_token(
                user_id=email,
                username=email,
                expires_delta=expires_delta,
                additional_claims={
                    "type": "magic_link",
                    "email": email,
                    "redirect_url": redirect_url,
                },
            )

            # Construct the magic link URL
            base_url = self.settings.base_url or "http://localhost:8000"
            magic_link = f"{base_url}/api/auth/magic?token={token}"

            self.logger.info(f"Generated magic link for {email}")
            return magic_link

        except AuthenticationError as e:
            self.logger.error(f"Failed to generate magic link for {email}: {e}")
            return None

    async def send_magic_link_email(
        self, email: str, expires_minutes: int = 15, redirect_url: str | None = None
    ) -> bool:
        """
        Send a magic link via email using the notification manager.

        Args:
            email: Email address to send the magic link to
            expires_minutes: Link expiration time in minutes
            redirect_url: URL to redirect to after authentication

        Returns:
            bool: True if email was sent successfully
        """
        if not self.notification_manager:
            self.logger.error("No notification manager available for magic link emails")
            return False

        magic_link = await self.generate_magic_link(email, expires_minutes, redirect_url)
        if not magic_link:
            return False

        try:
            success = await self.notification_manager.send_magic_link_email(
                to_email=email, magic_link=magic_link, expires_minutes=expires_minutes
            )

            if success:
                self.logger.info(f"Magic link email sent to {email}")
            else:
                self.logger.error(f"Failed to send magic link email to {email}")

            return success

        except Exception as e:
            self.logger.error(f"Error sending magic link email to {email}: {e}")
            return False

    async def validate_magic_link(self, token: str) -> dict[str, Any] | None:
        """
        Validate a magic link token.

        Args:
            token: The magic link token to validate

        Returns:
            Optional[Dict[str, Any]]: User info if valid, None otherwise
        """
        try:
            payload = self.validate_token(token)

            # Verify this is a magic link token
            if payload.get("type") != "magic_link":
                self.logger.warning("Token is not a magic link token")
                return None

            email = payload.get("email")
            if not email:
                self.logger.warning("Magic link token missing email")
                return None

            self.logger.info(f"Valid magic link token for {email}")
            return {
                "email": email,
                "user_id": payload.get("sub"),
                "redirect_url": payload.get("redirect_url"),
            }

        except InvalidTokenError as e:
            self.logger.warning(f"Invalid magic link token: {e}")
            return None

    def is_authenticated_request(self, token: str | None) -> bool:
        """
        Check if a request is authenticated based on the current mode.

        Args:
            token: Authorization token from the request

        Returns:
            bool: True if the request should be allowed
        """
        if self.auth_mode == AuthMode.NONE:
            # No authentication required
            return True

        if not token:
            return False

        try:
            self.validate_token(token)
            return True
        except InvalidTokenError:
            return False

    async def get_stats(self) -> dict[str, Any]:
        """
        Get authentication manager statistics.

        Returns:
            Dict[str, Any]: Statistics about the authentication system
        """
        stats = {
            "auth_mode": self.auth_mode.value,
            "jwt_available": JWT_AVAILABLE,
            "secret_key_configured": bool(self.settings.secret_key),
            "notification_manager_available": self.notification_manager is not None,
            "admin_configured": bool(self._admin_credentials)
            if self.auth_mode == AuthMode.SINGLE_USER
            else None,
        }

        if self.auth_mode == AuthMode.SINGLE_USER and self._admin_credentials:
            stats["admin_username"] = self._admin_credentials.get("username")
            stats["admin_created_at"] = self._admin_credentials.get("created_at")

        return stats
