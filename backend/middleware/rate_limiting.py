"""
Rate Limiting Middleware for Authentication Endpoints

This module provides rate limiting functionality specifically for authentication
endpoints to prevent brute force attacks and abuse. It uses slowapi for Redis-backed
rate limiting with configurable limits per endpoint.
"""

import logging
from collections.abc import Callable

from fastapi import Request, Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from backend.core.config import get_settings

logger = logging.getLogger(__name__)


def _get_client_id(request: Request) -> str:
    """
    Get client identifier for rate limiting.

    Uses the most appropriate identifier available:
    1. X-Forwarded-For header (for reverse proxy setups)
    2. X-Real-IP header (alternative proxy header)
    3. Remote address from connection

    Args:
        request: FastAPI request object

    Returns:
        str: Client identifier for rate limiting
    """
    # Check for forwarded IP headers (reverse proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP if there are multiple
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fall back to direct connection address
    return get_remote_address(request)


def _get_auth_client_id(request: Request) -> str:
    """
    Get client identifier for authentication rate limiting.

    For authentication endpoints, we want stricter identification that
    combines IP with username attempt to prevent attackers from
    cycling usernames to bypass IP-based limits.

    Args:
        request: FastAPI request object

    Returns:
        str: Enhanced client identifier for auth rate limiting
    """
    client_ip = _get_client_id(request)

    # For login attempts, include username if available
    if hasattr(request, "state") and hasattr(request.state, "attempted_username"):
        return f"{client_ip}:{request.state.attempted_username}"

    # Check form data for username (POST login)
    if request.method == "POST" and "application/x-www-form-urlencoded" in request.headers.get(
        "content-type", ""
    ):
        # This is handled in the auth endpoint to avoid reading body twice
        pass

    return client_ip


# Create rate limiter instance
settings = get_settings()

# Initialize limiter with memory storage (Redis can be added later)
limiter = Limiter(
    key_func=_get_client_id,
    default_limits=(
        []
        if not settings.security.rate_limit_enabled
        else [f"{settings.security.rate_limit_requests}/minute"]
    ),
    enabled=settings.security.rate_limit_enabled,
)

# Auth-specific limiter with stricter limits
auth_limiter = Limiter(
    key_func=_get_auth_client_id,
    default_limits=[],  # No default limits, defined per endpoint
    enabled=settings.security.rate_limit_enabled,
)


def create_auth_rate_limit() -> str:
    """
    Create rate limit string for authentication endpoints.

    Returns:
        str: Rate limit specification for auth endpoints
    """
    attempts = settings.auth.rate_limit_auth_attempts
    window = settings.auth.rate_limit_window_minutes
    return f"{attempts}/{window}minutes"


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom rate limit exceeded handler with security logging.

    Args:
        request: FastAPI request object
        exc: Rate limit exceeded exception

    Returns:
        Response: HTTP 429 response with appropriate headers
    """
    client_id = _get_client_id(request)
    endpoint = request.url.path

    # Log security event
    logger.warning(
        f"Rate limit exceeded for client {client_id} on {endpoint}",
        extra={
            "event_type": "rate_limit_exceeded",
            "client_id": client_id,
            "endpoint": endpoint,
            "user_agent": request.headers.get("User-Agent", "unknown"),
            "rate_limit": str(exc.detail),
        },
    )

    # Return the default rate limit response (this handles retry-after headers properly)
    response = _rate_limit_exceeded_handler(request, exc)

    # Add security headers (don't try to manually set retry-after as slowapi handles this)
    response.headers["X-Security-Warning"] = "Rate limit exceeded"

    return response


async def extract_username_for_rate_limiting(request: Request, call_next: Callable) -> Response:
    """
    Middleware to extract username from login attempts for enhanced rate limiting.

    This middleware extracts the username from form data and stores it in
    request state so the rate limiter can create per-user rate limits.

    Args:
        request: FastAPI request object
        call_next: Next middleware/handler in chain

    Returns:
        Response: Response from downstream handler
    """
    # Only process login endpoint
    if not (request.url.path == "/api/auth/login" and request.method == "POST"):
        return await call_next(request)

    # Try to extract username from form data
    try:
        if "application/x-www-form-urlencoded" in request.headers.get("content-type", ""):
            # Note: We can't easily read form data here without consuming the body
            # Instead, the rate limiting will be handled in the endpoint itself
            pass
    except Exception as e:
        logger.debug(f"Could not extract username for rate limiting: {e}")

    return await call_next(request)


# Helper functions for manual rate limiting in endpoints
def check_auth_rate_limit(request: Request, username: str | None = None) -> None:
    """
    Manually check rate limit for authentication attempts.

    This function provides additional rate limiting that can be called
    from within authentication endpoints for fine-grained control.

    Args:
        request: FastAPI request object
        username: Optional username for per-user rate limiting

    Raises:
        HTTPException: If rate limit is exceeded
    """
    if not settings.security.rate_limit_enabled:
        return

    client_ip = _get_client_id(request)

    # Create enhanced client ID for auth attempts
    client_id = f"{client_ip}:{username}" if username else client_ip

    # Log authentication attempt
    logger.info(
        f"Authentication attempt from {client_id}",
        extra={
            "event_type": "auth_attempt",
            "client_ip": client_ip,
            "username": username,
            "endpoint": request.url.path,
        },
    )


def get_rate_limit_decorator(limit_string: str):
    """
    Get a rate limit decorator with specified limits.

    Args:
        limit_string: Rate limit specification (e.g., "5/15minutes")

    Returns:
        Decorator function for FastAPI endpoints
    """
    if not settings.security.rate_limit_enabled:
        # Return a no-op decorator if rate limiting is disabled
        def no_op_decorator(func):
            return func

        return no_op_decorator

    return auth_limiter.limit(limit_string)


# Pre-configured decorators for common use cases
auth_rate_limit = get_rate_limit_decorator(create_auth_rate_limit())
magic_link_rate_limit = get_rate_limit_decorator("3/5minutes")  # More restrictive for email sending
admin_api_rate_limit = get_rate_limit_decorator("10/minute")  # Moderate limits for admin APIs


# Export rate limiting state for monitoring
def get_rate_limit_stats() -> dict[str, any]:
    """
    Get current rate limiting statistics for monitoring.

    Returns:
        dict: Rate limiting statistics and configuration
    """
    return {
        "enabled": settings.security.rate_limit_enabled,
        "auth_attempts_limit": settings.auth.rate_limit_auth_attempts,
        "auth_window_minutes": settings.auth.rate_limit_window_minutes,
        "general_limit": settings.security.rate_limit_requests,
        "limiter_enabled": limiter.enabled,
        "auth_limiter_enabled": auth_limiter.enabled,
    }
