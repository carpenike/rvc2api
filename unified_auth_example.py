"""
Example of a more unified authentication approach.

This shows how we could create a shared auth service that both
HTTP middleware and WebSocket handlers could use.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from fastapi import Request, WebSocket
from backend.services.auth_manager import AuthManager, AuthMode


class AuthContext(ABC):
    """Base class for authentication context (HTTP or WebSocket)."""

    @abstractmethod
    def get_token(self) -> Optional[str]:
        """Extract authentication token from the context."""
        pass

    @abstractmethod
    async def accept_unauthenticated(self, user_info: Dict[str, Any]) -> None:
        """Accept connection without authentication."""
        pass

    @abstractmethod
    async def reject_authentication(self, reason: str) -> None:
        """Reject connection due to authentication failure."""
        pass


class HTTPAuthContext(AuthContext):
    """HTTP request authentication context."""

    def __init__(self, request: Request):
        self.request = request

    def get_token(self) -> Optional[str]:
        # Extract from Authorization header
        auth_header = self.request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]
        return None

    async def accept_unauthenticated(self, user_info: Dict[str, Any]) -> None:
        # Set user info in request state
        self.request.state.user = user_info

    async def reject_authentication(self, reason: str) -> None:
        # This would raise HTTPException in actual implementation
        raise Exception(f"HTTP Auth failed: {reason}")


class WebSocketAuthContext(AuthContext):
    """WebSocket authentication context."""

    def __init__(self, websocket: WebSocket):
        self.websocket = websocket

    def get_token(self) -> Optional[str]:
        # Extract from query parameters
        try:
            scope = self.websocket.scope
            query_string = scope.get("query_string", b"").decode()
            if query_string:
                from urllib.parse import parse_qs
                query_params = parse_qs(query_string)
                token_list = query_params.get("token", [])
                if token_list:
                    return token_list[0]
        except Exception:
            pass
        return None

    async def accept_unauthenticated(self, user_info: Dict[str, Any]) -> None:
        # Accept WebSocket connection
        await self.websocket.accept()

    async def reject_authentication(self, reason: str) -> None:
        # Close WebSocket with auth failure code
        await self.websocket.close(code=1008)


class UnifiedAuthService:
    """Unified authentication service for both HTTP and WebSocket."""

    def __init__(self, auth_manager: Optional[AuthManager] = None):
        self.auth_manager = auth_manager

    async def authenticate(
        self,
        context: AuthContext,
        require_auth: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Authenticate using the provided context.

        This method works for both HTTP requests and WebSocket connections.
        """
        # Skip authentication if no auth manager available
        if not self.auth_manager:
            user_info = {
                "user_id": "admin",
                "username": "admin",
                "email": "admin@localhost",
                "role": "admin",
                "authenticated": True,
            }
            await context.accept_unauthenticated(user_info)
            return user_info

        # Skip authentication if mode is NONE
        if self.auth_manager.auth_mode == AuthMode.NONE:
            user_info = {
                "user_id": "admin",
                "username": "admin",
                "email": "admin@localhost",
                "role": "admin",
                "authenticated": True,
            }
            await context.accept_unauthenticated(user_info)
            return user_info

        # Extract token
        token = context.get_token()

        if not token:
            if require_auth:
                await context.reject_authentication("Missing authentication token")
                return None
            else:
                await context.accept_unauthenticated({"authenticated": False})
                return None

        try:
            # Validate token
            payload = self.auth_manager.verify_access_token(token)
            user_info = {
                "user_id": payload.get("sub"),
                "username": payload.get("username"),
                "email": payload.get("email"),
                "role": payload.get("role", "user"),
                "authenticated": True,
                "token_exp": payload.get("exp"),
            }
            await context.accept_unauthenticated(user_info)
            return user_info

        except Exception as e:
            await context.reject_authentication(f"Invalid token: {str(e)}")
            return None


# Usage examples:

async def http_middleware_with_unified_auth(request: Request, call_next):
    """HTTP middleware using unified auth service."""
    auth_service = UnifiedAuthService(get_auth_manager())
    context = HTTPAuthContext(request)
    user_info = await auth_service.authenticate(context, require_auth=True)
    return await call_next(request)


async def websocket_handler_with_unified_auth(websocket: WebSocket):
    """WebSocket handler using unified auth service."""
    auth_service = UnifiedAuthService(get_auth_manager())
    context = WebSocketAuthContext(websocket)
    user_info = await auth_service.authenticate(context, require_auth=True)

    if not user_info:
        return  # Connection already closed by auth service

    # Continue with WebSocket logic...
    try:
        while True:
            message = await websocket.receive_text()
            # Handle message...
    except Exception:
        pass


def get_auth_manager():
    """Get auth manager (placeholder)."""
    return None
