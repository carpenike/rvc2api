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
    import pyotp
    from passlib.context import CryptContext

    JWT_AVAILABLE = True
    BCRYPT_AVAILABLE = True
    TOTP_AVAILABLE = True
except ImportError as e:
    JWT_AVAILABLE = False
    BCRYPT_AVAILABLE = False
    TOTP_AVAILABLE = False

    logging.error(f"Authentication dependencies missing: {e}. Please install with: poetry install")

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


class AccountLockedError(AuthenticationError):
    """Raised when an account is locked due to too many failed attempts."""

    def __init__(self, message: str, lockout_until: datetime, attempts: int):
        super().__init__(message)
        self.lockout_until = lockout_until
        self.attempts = attempts


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
        if JWT_AVAILABLE and BCRYPT_AVAILABLE:
            self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        else:
            self.pwd_context = None
            if not JWT_AVAILABLE:
                self.logger.error("JWT dependencies not available - authentication disabled")
            if not BCRYPT_AVAILABLE:
                self.logger.error("bcrypt not available - password hashing will fail")
            raise RuntimeError(
                "Authentication dependencies missing. Please install with: poetry install"
            )

        # Determine authentication mode
        self.auth_mode = self._detect_auth_mode()
        self.logger.info(f"Authentication mode detected: {self.auth_mode}")

        # Initialize admin credentials if needed
        self._admin_credentials = {}
        self._generated_password = None  # Store auto-generated password temporarily

        # Initialize refresh token storage (in-memory for now, could be Redis/DB later)
        self._refresh_tokens: dict[
            str, dict[str, Any]
        ] = {}  # {token_id: {user_id, expires, created}}

        # Initialize account lockout tracking (in-memory for now, could be Redis/DB later)
        self._failed_attempts: dict[
            str, dict[str, Any]
        ] = {}  # {user_id: {count, last_attempt, lockout_until, escalation_level}}
        self._successful_logins: dict[str, int] = {}  # {user_id: consecutive_success_count}

        # Initialize MFA storage (in-memory for now, could be Redis/DB later)
        self._user_mfa_secrets: dict[
            str, dict[str, Any]
        ] = {}  # {user_id: {secret, backup_codes, recovery_codes, enabled}}
        self._used_backup_codes: dict[str, set[str]] = {}  # {user_id: {used_backup_codes}}

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
            # Store the generated password temporarily for one-time display via API
            self._generated_password = password
            self.logger.critical(f"Auto-generated admin credentials for username: {username}")
            self.logger.critical(
                "IMPORTANT: Use the /api/auth/admin/credentials endpoint to retrieve the password. "
                "It will only be displayed once for security reasons."
            )

        # Hash the password using bcrypt (dependencies are guaranteed to be available)
        password_hash = self.pwd_context.hash(password)
        self._admin_credentials = {
            "username": username,
            "password_hash": password_hash,
            "created_at": datetime.now(UTC),
            "password_auto_generated": not bool(self.settings.admin_password),
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
                to_encode,
                self.settings.secret_key,
                algorithm=self.settings.jwt_algorithm,
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

    def generate_refresh_token(
        self,
        user_id: str,
        username: str = "",
        additional_claims: dict[str, Any] | None = None,
    ) -> str:
        """
        Generate a refresh token for a user.

        Args:
            user_id: Unique identifier for the user
            username: Username for the user (optional)
            additional_claims: Additional claims to include in the token

        Returns:
            str: The encoded refresh token

        Raises:
            AuthenticationError: If JWT is not available or refresh tokens disabled
        """
        if not self.settings.enable_refresh_tokens:
            raise AuthenticationError("Refresh tokens are disabled")

        if not JWT_AVAILABLE or not self.settings.refresh_token_secret:
            raise AuthenticationError("Refresh token generation not available")

        # Generate unique token ID for tracking
        import secrets

        token_id = secrets.token_urlsafe(16)

        expires_delta = timedelta(days=self.settings.refresh_token_expire_days)
        expire = datetime.now(UTC) + expires_delta

        to_encode = {
            "sub": str(user_id),
            "username": username,
            "exp": expire,
            "iat": datetime.now(UTC),
            "iss": "coachiq",
            "aud": "coachiq-refresh",
            "jti": token_id,  # JWT ID for tracking
            "token_type": "refresh",
        }

        if additional_claims:
            to_encode.update(additional_claims)

        try:
            encoded_jwt = jwt.encode(
                to_encode,
                self.settings.refresh_token_secret,
                algorithm=self.settings.jwt_algorithm,
            )

            # Store refresh token metadata for tracking/revocation
            self._refresh_tokens[token_id] = {
                "user_id": str(user_id),
                "username": username,
                "expires": expire,
                "created": datetime.now(UTC),
                "revoked": False,
            }

            return encoded_jwt
        except Exception as e:
            self.logger.error(f"Failed to generate refresh token: {e}")
            raise AuthenticationError("Refresh token generation failed") from e

    def validate_refresh_token(self, token: str) -> dict[str, Any]:
        """
        Validate and decode a refresh token.

        Args:
            token: The refresh token to validate

        Returns:
            dict[str, Any]: The decoded token payload

        Raises:
            InvalidTokenError: If the token is invalid, expired, or revoked
        """
        if not self.settings.enable_refresh_tokens:
            raise InvalidTokenError("Refresh tokens are disabled")

        if not JWT_AVAILABLE or not self.settings.refresh_token_secret:
            raise InvalidTokenError("Refresh token validation not available")

        try:
            payload = jwt.decode(
                token,
                self.settings.refresh_token_secret,
                algorithms=[self.settings.jwt_algorithm],
                audience="coachiq-refresh",
                issuer="coachiq",
            )

            # Check if token is revoked
            token_id = payload.get("jti")
            if token_id and token_id in self._refresh_tokens:
                token_info = self._refresh_tokens[token_id]
                if token_info.get("revoked", False):
                    raise InvalidTokenError("Refresh token has been revoked")

            return payload
        except jwt.ExpiredSignatureError as e:
            # Clean up expired token from storage
            token_id = jwt.decode(token, options={"verify_signature": False}).get("jti")
            if token_id and token_id in self._refresh_tokens:
                del self._refresh_tokens[token_id]
            raise InvalidTokenError("Refresh token has expired") from e
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError(f"Invalid refresh token: {e}") from e

    def revoke_refresh_token(self, token: str) -> bool:
        """
        Revoke a refresh token.

        Args:
            token: The refresh token to revoke

        Returns:
            bool: True if token was revoked, False if not found
        """
        try:
            # Use same verification as validate_refresh_token to ensure consistency
            payload = jwt.decode(
                token,
                self.settings.refresh_token_secret,
                algorithms=[self.settings.jwt_algorithm],
                audience="coachiq-refresh",
                issuer="coachiq",
            )
            token_id = payload.get("jti")

            if token_id:
                # Initialize the dictionary entry if it doesn't exist (edge case)
                if token_id not in self._refresh_tokens:
                    self._refresh_tokens[token_id] = {}

                self._refresh_tokens[token_id]["revoked"] = True
                self.logger.info(f"Refresh token revoked: {token_id}")
                return True

            return False
        except Exception as e:
            self.logger.warning(f"Failed to revoke refresh token: {e}")
            return False

    def revoke_all_user_refresh_tokens(self, user_id: str) -> int:
        """
        Revoke all refresh tokens for a specific user.

        Args:
            user_id: User ID whose tokens should be revoked

        Returns:
            int: Number of tokens revoked
        """
        revoked_count = 0
        for _token_id, token_info in self._refresh_tokens.items():
            if token_info["user_id"] == str(user_id) and not token_info.get("revoked", False):
                token_info["revoked"] = True
                revoked_count += 1

        if revoked_count > 0:
            self.logger.info(f"Revoked {revoked_count} refresh tokens for user {user_id}")

        return revoked_count

    def refresh_access_token(self, refresh_token: str) -> tuple[str, str]:
        """
        Generate a new access token using a valid refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            tuple[str, str]: New access token and new refresh token

        Raises:
            InvalidTokenError: If refresh token is invalid
            AuthenticationError: If token generation fails
        """
        # Validate the refresh token
        payload = self.validate_refresh_token(refresh_token)

        user_id = payload.get("sub")
        username = payload.get("username", "")

        if not user_id:
            raise InvalidTokenError("Invalid refresh token payload")

        # Generate new access token
        access_token = self.generate_token(
            user_id=user_id,
            username=username,
            additional_claims={
                "email": payload.get("email"),
                "role": payload.get("role", "user"),
                "mode": payload.get("mode", self.auth_mode.value),
            },
        )

        # Generate new refresh token (token rotation for security)
        new_refresh_token = self.generate_refresh_token(
            user_id=user_id,
            username=username,
            additional_claims={
                "email": payload.get("email"),
                "role": payload.get("role", "user"),
                "mode": payload.get("mode", self.auth_mode.value),
            },
        )

        # Revoke the old refresh token
        self.revoke_refresh_token(refresh_token)

        return access_token, new_refresh_token

    def cleanup_expired_refresh_tokens(self) -> int:
        """
        Clean up expired refresh tokens from storage.

        Returns:
            int: Number of tokens cleaned up
        """
        current_time = datetime.now(UTC)
        expired_tokens = []

        for token_id, token_info in self._refresh_tokens.items():
            if token_info["expires"] < current_time:
                expired_tokens.append(token_id)

        for token_id in expired_tokens:
            del self._refresh_tokens[token_id]

        if expired_tokens:
            self.logger.info(f"Cleaned up {len(expired_tokens)} expired refresh tokens")

        return len(expired_tokens)

    async def authenticate_admin_with_refresh(
        self, username: str, password: str
    ) -> tuple[str, str] | None:
        """
        Authenticate admin user and return both access and refresh tokens.

        Args:
            username: Admin username
            password: Admin password

        Returns:
            Optional[tuple[str, str]]: (access_token, refresh_token) if successful, None otherwise

        Raises:
            AccountLockedError: If the account is locked due to failed attempts
        """
        if self.auth_mode != AuthMode.SINGLE_USER:
            self.logger.warning(f"Admin authentication called in {self.auth_mode} mode")
            return None

        if not self._admin_credentials:
            self.logger.error("No admin credentials configured")
            return None

        # Check if account is locked
        is_locked, lockout_until = self.is_account_locked(username)
        if is_locked:
            attempt_data = self._failed_attempts.get(self._get_user_key(username), {})
            raise AccountLockedError(
                f"Account locked until {lockout_until.isoformat()}",
                lockout_until,
                attempt_data.get("count", 0),
            )

        # Verify username
        if username != self._admin_credentials["username"]:
            self.logger.warning(f"Invalid admin username: {username}")
            self.record_failed_attempt(username)
            return None

        # Verify password using bcrypt
        if not self.pwd_context.verify(password, self._admin_credentials["password_hash"]):
            self.logger.warning("Invalid admin password")
            self.record_failed_attempt(username)
            return None

        # Generate both tokens
        try:
            additional_claims = {"role": "admin", "mode": "single-user"}

            access_token = self.generate_token(
                user_id="admin",
                username=username,
                additional_claims=additional_claims,
            )

            refresh_token = ""
            if self.settings.enable_refresh_tokens:
                refresh_token = self.generate_refresh_token(
                    user_id="admin",
                    username=username,
                    additional_claims=additional_claims,
                )

            # Record successful login for lockout tracking
            self.record_successful_login(username)

            self.logger.info(f"Admin user authenticated with refresh: {username}")
            return access_token, refresh_token
        except AuthenticationError as e:
            self.logger.error(f"Failed to generate admin tokens: {e}")
            return None

    async def authenticate_admin(self, username: str, password: str) -> str | None:
        """
        Authenticate admin user in single-user mode.

        Args:
            username: Admin username
            password: Admin password

        Returns:
            Optional[str]: JWT token if authentication successful, None otherwise

        Raises:
            AccountLockedError: If the account is locked due to failed attempts
        """
        if self.auth_mode != AuthMode.SINGLE_USER:
            self.logger.warning(f"Admin authentication called in {self.auth_mode} mode")
            return None

        if not self._admin_credentials:
            self.logger.error("No admin credentials configured")
            return None

        # Check if account is locked
        is_locked, lockout_until = self.is_account_locked(username)
        if is_locked:
            attempt_data = self._failed_attempts.get(self._get_user_key(username), {})
            raise AccountLockedError(
                f"Account locked until {lockout_until.isoformat()}",
                lockout_until,
                attempt_data.get("count", 0),
            )

        # Verify username
        if username != self._admin_credentials["username"]:
            self.logger.warning(f"Invalid admin username: {username}")
            self.record_failed_attempt(username)
            return None

        # Verify password using bcrypt
        if not self.pwd_context.verify(password, self._admin_credentials["password_hash"]):
            self.logger.warning("Invalid admin password")
            self.record_failed_attempt(username)
            return None

        # Generate token
        try:
            token = self.generate_token(
                user_id="admin",
                username=username,
                additional_claims={"role": "admin", "mode": "single-user"},
            )

            # Record successful login for lockout tracking
            self.record_successful_login(username)

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

    async def get_generated_credentials(self) -> dict[str, str] | None:
        """
        Get auto-generated admin credentials (one-time display only).

        This method returns the credentials only once for security reasons.
        After calling this method, the credentials are cleared from memory.

        Returns:
            Optional[Dict[str, str]]: Admin credentials if available, None otherwise
        """
        if (
            self.auth_mode != AuthMode.SINGLE_USER
            or not self._generated_password
            or not self._admin_credentials
        ):
            return None

        # Return credentials once
        credentials = {
            "username": self._admin_credentials["username"],
            "password": self._generated_password,
            "created_at": self._admin_credentials["created_at"].isoformat(),
            "warning": "Save these credentials immediately! They will not be displayed again.",
        }

        # Clear the generated password from memory for security
        self._generated_password = None

        self.logger.info("Auto-generated admin credentials retrieved via API")
        return credentials

    async def has_generated_credentials(self) -> bool:
        """
        Check if there are auto-generated credentials available for retrieval.

        Returns:
            bool: True if credentials are available for one-time display
        """
        return (
            self.auth_mode == AuthMode.SINGLE_USER
            and self._generated_password is not None
            and self._admin_credentials.get("password_auto_generated", False)
        )

    async def get_stats(self) -> dict[str, Any]:
        """
        Get authentication manager statistics.

        Returns:
            Dict[str, Any]: Statistics about the authentication system
        """
        stats = {
            "auth_mode": self.auth_mode.value,
            "jwt_available": JWT_AVAILABLE,
            "bcrypt_available": BCRYPT_AVAILABLE,
            "secret_key_configured": bool(self.settings.secret_key),
            "notification_manager_available": self.notification_manager is not None,
            "admin_configured": (
                bool(self._admin_credentials) if self.auth_mode == AuthMode.SINGLE_USER else None
            ),
            "has_generated_credentials": await self.has_generated_credentials(),
        }

        if self.auth_mode == AuthMode.SINGLE_USER and self._admin_credentials:
            stats["admin_username"] = self._admin_credentials.get("username")
            stats["admin_created_at"] = self._admin_credentials.get("created_at")
            stats["password_auto_generated"] = self._admin_credentials.get(
                "password_auto_generated", False
            )

        return stats

    # Multi-Factor Authentication (MFA) methods

    def is_mfa_available(self) -> bool:
        """Check if MFA dependencies are available."""
        return TOTP_AVAILABLE and getattr(self.settings, "enable_mfa", False)

    def generate_mfa_secret(self, user_id: str) -> dict[str, Any]:
        """
        Generate a new TOTP secret for a user.

        Args:
            user_id: User ID to generate secret for

        Returns:
            dict[str, Any]: Secret and QR code information

        Raises:
            AuthenticationError: If MFA is not available
        """
        if not self.is_mfa_available():
            raise AuthenticationError("MFA not available - missing dependencies or disabled")

        # Generate TOTP secret
        secret = pyotp.random_base32()

        # Get MFA settings from feature flags
        issuer = getattr(self.settings, "mfa_totp_issuer", "CoachIQ")
        digits = getattr(self.settings, "mfa_totp_digits", 6)

        # Create TOTP instance
        totp = pyotp.TOTP(secret, digits=digits)

        # Generate provisioning URI for QR code
        provisioning_uri = totp.provisioning_uri(name=user_id, issuer_name=issuer)

        # Generate QR code image
        qr_code_data = self._generate_qr_code(provisioning_uri)

        # Generate backup codes
        backup_codes = self._generate_backup_codes()

        # Store secret (but don't enable MFA yet)
        self._user_mfa_secrets[user_id] = {
            "secret": secret,
            "backup_codes": backup_codes,
            "recovery_codes": [],
            "enabled": False,
            "created_at": datetime.now(UTC),
            "last_used": None,
        }

        self.logger.info(f"Generated MFA secret for user {user_id}")

        return {
            "secret": secret,
            "qr_code": qr_code_data,
            "provisioning_uri": provisioning_uri,
            "backup_codes": backup_codes,
            "issuer": issuer,
        }

    def _generate_qr_code(self, provisioning_uri: str) -> str:
        """Generate base64-encoded QR code image."""
        import base64
        import io

        import qrcode

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        img_buffer = io.BytesIO()
        img.save(img_buffer, format="PNG")
        img_str = base64.b64encode(img_buffer.getvalue()).decode()

        return f"data:image/png;base64,{img_str}"

    def _generate_backup_codes(self) -> list[str]:
        """Generate backup codes for MFA recovery."""
        backup_codes_count = getattr(self.settings, "mfa_backup_codes_count", 10)
        backup_code_length = getattr(self.settings, "mfa_backup_code_length", 8)

        backup_codes = []
        for _ in range(backup_codes_count):
            # Generate alphanumeric backup codes
            code = secrets.token_hex(backup_code_length // 2).upper()
            backup_codes.append(code)

        return backup_codes

    def verify_mfa_setup(self, user_id: str, totp_code: str) -> bool:
        """
        Verify TOTP code during MFA setup and enable MFA.

        Args:
            user_id: User ID
            totp_code: TOTP code from authenticator app

        Returns:
            bool: True if verification successful and MFA enabled

        Raises:
            AuthenticationError: If MFA not available or user not found
        """
        if not self.is_mfa_available():
            raise AuthenticationError("MFA not available")

        if user_id not in self._user_mfa_secrets:
            raise AuthenticationError("MFA setup not initiated for user")

        mfa_data = self._user_mfa_secrets[user_id]
        secret = mfa_data["secret"]

        # Verify TOTP code
        if self._verify_totp_code(secret, totp_code):
            # Enable MFA for the user
            mfa_data["enabled"] = True
            mfa_data["last_used"] = datetime.now(UTC)

            self.logger.info(f"MFA enabled for user {user_id}")
            return True

        return False

    def verify_mfa_code(self, user_id: str, code: str) -> bool:
        """
        Verify MFA code (TOTP or backup code).

        Args:
            user_id: User ID
            code: TOTP code or backup code

        Returns:
            bool: True if code is valid

        Raises:
            AuthenticationError: If MFA not available or not enabled for user
        """
        if not self.is_mfa_available():
            raise AuthenticationError("MFA not available")

        if user_id not in self._user_mfa_secrets:
            raise AuthenticationError("MFA not set up for user")

        mfa_data = self._user_mfa_secrets[user_id]

        if not mfa_data["enabled"]:
            raise AuthenticationError("MFA not enabled for user")

        # Try TOTP first
        if self._verify_totp_code(mfa_data["secret"], code):
            mfa_data["last_used"] = datetime.now(UTC)
            return True

        # Try backup codes
        if self._verify_backup_code(user_id, code):
            mfa_data["last_used"] = datetime.now(UTC)
            return True

        return False

    def _verify_totp_code(self, secret: str, code: str) -> bool:
        """Verify TOTP code against secret."""
        digits = getattr(self.settings, "mfa_totp_digits", 6)
        window = getattr(self.settings, "mfa_totp_window", 1)

        totp = pyotp.TOTP(secret, digits=digits)
        return totp.verify(code, valid_window=window)

    def _verify_backup_code(self, user_id: str, code: str) -> bool:
        """Verify backup code and mark as used."""
        mfa_data = self._user_mfa_secrets.get(user_id)
        if not mfa_data:
            return False

        backup_codes = mfa_data.get("backup_codes", [])
        used_codes = self._used_backup_codes.setdefault(user_id, set())

        # Check if code is valid and not already used
        if code.upper() in backup_codes and code.upper() not in used_codes:
            used_codes.add(code.upper())
            self.logger.info(f"Backup code used for user {user_id}")

            # Check if we need to regenerate backup codes
            regeneration_threshold = getattr(
                self.settings, "mfa_backup_code_regeneration_threshold", 3
            )
            if len(used_codes) >= len(backup_codes) - regeneration_threshold:
                self._regenerate_backup_codes(user_id)

            return True

        return False

    def _regenerate_backup_codes(self, user_id: str) -> list[str]:
        """Regenerate backup codes for a user."""
        if user_id not in self._user_mfa_secrets:
            return []

        new_backup_codes = self._generate_backup_codes()
        self._user_mfa_secrets[user_id]["backup_codes"] = new_backup_codes

        # Reset used codes
        self._used_backup_codes[user_id] = set()

        self.logger.info(f"Regenerated backup codes for user {user_id}")
        return new_backup_codes

    def disable_mfa(self, user_id: str, admin_user: str = "system") -> bool:
        """
        Disable MFA for a user (admin function).

        Args:
            user_id: User ID to disable MFA for
            admin_user: Admin performing the action

        Returns:
            bool: True if MFA was disabled, False if not enabled
        """
        if user_id not in self._user_mfa_secrets:
            return False

        was_enabled = self._user_mfa_secrets[user_id].get("enabled", False)

        # Clear MFA data
        del self._user_mfa_secrets[user_id]
        if user_id in self._used_backup_codes:
            del self._used_backup_codes[user_id]

        if was_enabled:
            self.logger.info(f"MFA disabled for user {user_id} by admin {admin_user}")
            return True

        return False

    def get_mfa_status(self, user_id: str) -> dict[str, Any]:
        """
        Get MFA status for a user.

        Args:
            user_id: User ID to check

        Returns:
            dict[str, Any]: MFA status information
        """
        mfa_data = self._user_mfa_secrets.get(user_id)

        if not mfa_data:
            return {
                "user_id": user_id,
                "mfa_enabled": False,
                "setup_initiated": False,
                "available": self.is_mfa_available(),
            }

        used_backup_codes = len(self._used_backup_codes.get(user_id, set()))
        total_backup_codes = len(mfa_data.get("backup_codes", []))

        return {
            "user_id": user_id,
            "mfa_enabled": mfa_data.get("enabled", False),
            "setup_initiated": True,
            "created_at": (
                mfa_data.get("created_at").isoformat() if mfa_data.get("created_at") else None
            ),
            "last_used": (
                mfa_data.get("last_used").isoformat() if mfa_data.get("last_used") else None
            ),
            "backup_codes_remaining": total_backup_codes - used_backup_codes,
            "backup_codes_total": total_backup_codes,
            "available": self.is_mfa_available(),
        }

    def get_backup_codes(self, user_id: str) -> list[str] | None:
        """
        Get backup codes for a user (one-time display).

        Args:
            user_id: User ID

        Returns:
            list[str] | None: Backup codes if available
        """
        mfa_data = self._user_mfa_secrets.get(user_id)
        if not mfa_data:
            return None

        return mfa_data.get("backup_codes", [])

    def regenerate_backup_codes(self, user_id: str) -> list[str] | None:
        """
        Regenerate backup codes for a user.

        Args:
            user_id: User ID

        Returns:
            list[str] | None: New backup codes if successful
        """
        if user_id not in self._user_mfa_secrets:
            return None

        return self._regenerate_backup_codes(user_id)

    def get_all_mfa_status(self) -> list[dict[str, Any]]:
        """
        Get MFA status for all users.

        Returns:
            list[dict[str, Any]]: List of MFA status for all users
        """
        all_users = set(self._user_mfa_secrets.keys())

        # Also include admin user if in single-user mode
        if self.auth_mode == AuthMode.SINGLE_USER and self._admin_credentials:
            all_users.add("admin")

        return [self.get_mfa_status(user_id) for user_id in sorted(all_users)]

    # Account lockout management methods

    def _get_user_key(self, username: str) -> str:
        """Generate consistent user key for lockout tracking."""
        return f"user:{username.lower()}"

    def is_account_locked(self, username: str) -> tuple[bool, datetime | None]:
        """
        Check if an account is currently locked.

        Args:
            username: Username to check

        Returns:
            tuple[bool, datetime | None]: (is_locked, lockout_expires)
        """
        if not self.settings.enable_account_lockout:
            return False, None

        user_key = self._get_user_key(username)
        attempt_data = self._failed_attempts.get(user_key)

        if not attempt_data:
            return False, None

        lockout_until = attempt_data.get("lockout_until")
        if not lockout_until:
            return False, None

        now = datetime.now(UTC)
        if now < lockout_until:
            return True, lockout_until
        else:
            # Lockout expired, clear it
            self._clear_expired_lockout(user_key)
            return False, None

    def _clear_expired_lockout(self, user_key: str) -> None:
        """Clear expired lockout data for a user."""
        if user_key in self._failed_attempts:
            attempt_data = self._failed_attempts[user_key]
            # Keep the escalation level but clear the lockout
            attempt_data["lockout_until"] = None
            attempt_data["count"] = 0

    def record_failed_attempt(self, username: str) -> None:
        """
        Record a failed login attempt and apply lockout if necessary.

        Args:
            username: Username that failed authentication
        """
        if not self.settings.enable_account_lockout:
            return

        user_key = self._get_user_key(username)
        now = datetime.now(UTC)

        # Get or initialize attempt data
        attempt_data = self._failed_attempts.setdefault(
            user_key,
            {
                "count": 0,
                "last_attempt": now,
                "lockout_until": None,
                "escalation_level": 0,
            },
        )

        # Increment failed attempt count
        attempt_data["count"] += 1
        attempt_data["last_attempt"] = now

        # Reset successful login count
        if user_key in self._successful_logins:
            del self._successful_logins[user_key]

        self.logger.warning(f"Failed login attempt {attempt_data['count']} for user: {username}")

        # Check if we need to apply lockout
        if attempt_data["count"] >= self.settings.max_failed_attempts:
            escalation_level = attempt_data["escalation_level"]

            # Calculate lockout duration with exponential backoff
            base_duration = self.settings.lockout_duration_minutes
            escalated_duration = base_duration * (
                self.settings.lockout_escalation_factor**escalation_level
            )

            # Cap at maximum duration
            max_duration = self.settings.max_lockout_duration_hours * 60
            lockout_minutes = min(escalated_duration, max_duration)

            lockout_until = now + timedelta(minutes=lockout_minutes)
            attempt_data["lockout_until"] = lockout_until
            attempt_data["escalation_level"] = escalation_level + 1

            self.logger.error(
                f"Account locked for user {username} until {lockout_until.isoformat()} "
                f"(duration: {lockout_minutes:.1f} minutes, escalation level: {escalation_level + 1})"
            )

    def record_successful_login(self, username: str) -> None:
        """
        Record a successful login and potentially reset lockout escalation.

        Args:
            username: Username that successfully authenticated
        """
        if not self.settings.enable_account_lockout:
            return

        user_key = self._get_user_key(username)

        # Clear any active lockout
        if user_key in self._failed_attempts:
            del self._failed_attempts[user_key]

        # Track consecutive successful logins
        success_count = self._successful_logins.get(user_key, 0) + 1
        self._successful_logins[user_key] = success_count

        # Reset escalation level after enough successful logins
        if success_count >= self.settings.lockout_reset_success_count:
            if user_key in self._failed_attempts:
                self._failed_attempts[user_key]["escalation_level"] = 0

            self.logger.info(
                f"Lockout escalation reset for user {username} after {success_count} successful logins"
            )

    def get_lockout_status(self, username: str) -> dict[str, Any]:
        """
        Get detailed lockout status for a user.

        Args:
            username: Username to check

        Returns:
            dict[str, Any]: Lockout status information
        """
        user_key = self._get_user_key(username)
        is_locked, lockout_until = self.is_account_locked(username)

        attempt_data = self._failed_attempts.get(user_key, {})
        success_count = self._successful_logins.get(user_key, 0)

        return {
            "username": username,
            "is_locked": is_locked,
            "lockout_until": lockout_until.isoformat() if lockout_until else None,
            "failed_attempts": attempt_data.get("count", 0),
            "escalation_level": attempt_data.get("escalation_level", 0),
            "last_attempt": (
                attempt_data.get("last_attempt").isoformat()
                if attempt_data.get("last_attempt")
                else None
            ),
            "consecutive_successful_logins": success_count,
            "lockout_enabled": self.settings.enable_account_lockout,
            "max_failed_attempts": self.settings.max_failed_attempts,
            "lockout_duration_minutes": self.settings.lockout_duration_minutes,
        }

    def unlock_account(self, username: str, admin_user: str = "system") -> bool:
        """
        Manually unlock an account (admin function).

        Args:
            username: Username to unlock
            admin_user: Admin performing the unlock

        Returns:
            bool: True if account was unlocked, False if not locked
        """
        user_key = self._get_user_key(username)

        if user_key not in self._failed_attempts:
            return False

        was_locked = self._failed_attempts[user_key].get("lockout_until") is not None

        # Clear all lockout data
        del self._failed_attempts[user_key]
        if user_key in self._successful_logins:
            del self._successful_logins[user_key]

        if was_locked:
            self.logger.info(f"Account unlocked for user {username} by admin {admin_user}")
            return True

        return False

    def get_all_lockout_status(self) -> list[dict[str, Any]]:
        """
        Get lockout status for all tracked users.

        Returns:
            list[dict[str, Any]]: List of lockout status for all users
        """
        all_users = set()

        # Collect all tracked usernames
        for user_key in self._failed_attempts:
            if user_key.startswith("user:"):
                username = user_key[5:]  # Remove "user:" prefix
                all_users.add(username)

        for user_key in self._successful_logins:
            if user_key.startswith("user:"):
                username = user_key[5:]  # Remove "user:" prefix
                all_users.add(username)

        return [self.get_lockout_status(username) for username in sorted(all_users)]
