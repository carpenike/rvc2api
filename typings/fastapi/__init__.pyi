"""
Type stub file for FastAPI to improve pylance type checking.

This file provides type hints for commonly used FastAPI components.
Uses Python 3.9+ typing syntax with | for unions and builtin collection types.

Note: The non-snake_case function name Body() is exempted from linting rules
in pyproject.toml using [tool.ruff.lint.per-file-ignores] configuration.
"""

from collections.abc import Callable
from typing import Any, Generic, TypeVar

# Types
T = TypeVar("T")

class Annotated(Generic[T]): ...

# BackgroundTasks class
class BackgroundTasks:
    def __init__(self) -> None: ...
    def add_task(self, func: Callable, *args: Any, **kwargs: Any) -> None: ...

# Request class
class Request:
    url: URL
    method: str
    app: Any

class URL:
    path: str

class Response:
    media_type: str | None
    status_code: int

    def __init__(
        self,
        content: Any = None,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        media_type: str | None = None,
    ) -> None: ...

# WebSocket classes
class WebSocket:
    client: Any
    async def accept(self) -> None: ...
    async def close(self, code: int = 1000) -> None: ...
    async def send_text(self, data: str) -> None: ...
    async def send_json(self, data: Any) -> None: ...
    async def send_bytes(self, data: bytes) -> None: ...
    async def receive_text(self) -> str: ...
    async def receive_json(self) -> Any: ...
    async def receive_bytes(self) -> bytes: ...

class WebSocketDisconnect(Exception):
    code: int
    def __init__(self, code: int = 1000) -> None: ...

class WebSocketException(Exception): ...

# Router class
class APIRouter:
    def __init__(
        self,
        *,
        prefix: str = "",
        tags: list[str] | None = None,
        dependencies: list[Any] | None = None,
        responses: dict[int | str, dict[str, Any]] | None = None,
        default_response_class: type[Response] | None = None,
        route_class: Any = None,
        on_startup: list[Any] | None = None,
        on_shutdown: list[Any] | None = None,
        deprecated: bool | None = None,
        include_in_schema: bool = True,
        redirect_slashes: bool = True,
        **kwargs: Any,
    ) -> None: ...
    def get(
        self,
        path: str,
        *,
        response_model: Any = None,
        status_code: int | None = None,
        tags: list[str] | None = None,
        summary: str | None = None,
        description: str | None = None,
        response_description: str = "Successful Response",
        **kwargs: Any,
    ) -> Any: ...
    def post(
        self,
        path: str,
        *,
        response_model: Any = None,
        status_code: int | None = None,
        tags: list[str] | None = None,
        summary: str | None = None,
        description: str | None = None,
        response_description: str = "Successful Response",
        **kwargs: Any,
    ) -> Any: ...
    def put(
        self,
        path: str,
        *,
        response_model: Any = None,
        status_code: int | None = None,
        tags: list[str] | None = None,
        summary: str | None = None,
        description: str | None = None,
        response_description: str = "Successful Response",
        **kwargs: Any,
    ) -> Any: ...
    def delete(
        self,
        path: str,
        *,
        response_model: Any = None,
        status_code: int | None = None,
        tags: list[str] | None = None,
        summary: str | None = None,
        description: str | None = None,
        response_description: str = "Successful Response",
        **kwargs: Any,
    ) -> Any: ...
    def websocket(
        self,
        path: str,
        *,
        name: str | None = None,
        **kwargs: Any,
    ) -> Any: ...
    def add_api_websocket_route(
        self,
        path: str,
        endpoint: Callable,
        *,
        name: str | None = None,
        **kwargs: Any,
    ) -> None: ...

# HTTP Exception class
class HTTPException(Exception):
    status_code: int
    detail: Any
    headers: dict[str, Any] | None

    def __init__(
        self, status_code: int, detail: Any = None, headers: dict[str, Any] | None = None
    ) -> None: ...

# Core FastAPI class
class FastAPI:
    state: Any

    def __init__(
        self,
        *,
        debug: bool = False,
        title: str = "FastAPI",
        description: str = "",
        version: str = "0.1.0",
        openapi_url: str | None = "/openapi.json",
        docs_url: str | None = "/docs",
        redoc_url: str | None = "/redoc",
        root_path: str = "",
        servers: list[dict[str, str]] | None = None,
        lifespan: Any = None,
    ) -> None: ...
    def mount(self, path: str, app: Any, name: str | None = None) -> None: ...
    def middleware(self, middleware_type: str) -> Any: ...
    def exception_handler(self, exc_class_or_status_code: Any) -> Any: ...
    def get(
        self,
        path: str,
        *,
        response_model: Any = None,
        status_code: int | None = None,
        tags: list[str] | None = None,
        summary: str | None = None,
        description: str | None = None,
        response_description: str = "Successful Response",
        **kwargs: Any,
    ) -> Any: ...
    def include_router(
        self,
        router: Any,
        *,
        prefix: str = "",
        tags: list[str] | None = None,
        dependencies: list[Any] | None = None,
        responses: dict[int | str, dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> None: ...

# Define the possible types for examples
examples_type = dict[str, Any] | list[Any] | dict[str, dict[str, str | dict[str, Any]]] | None

# Parameter declarations
def Body(
    default: Any = ...,
    *,
    embed: bool = False,
    media_type: str = "application/json",
    title: str | None = None,
    description: str | None = None,
    gt: float | None = None,
    ge: float | None = None,
    lt: float | None = None,
    le: float | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
    regex: str | None = None,
    example: Any = None,
    examples: examples_type = None,
) -> Any: ...
def Query(
    default: Any = ...,
    *,
    title: str | None = None,
    description: str | None = None,
    gt: float | None = None,
    ge: float | None = None,
    lt: float | None = None,
    le: float | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
    regex: str | None = None,
    alias: str | None = None,
    deprecated: bool = False,
    include_in_schema: bool = True,
    example: Any = None,
    examples: examples_type = None,
) -> Any: ...

# For backward compatibility
body_param: Any = Body

# Response classes
class JSONResponse(Response):
    def __init__(
        self,
        content: Any,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        media_type: str = "application/json",
    ) -> None: ...

class HTMLResponse(Response): ...
class PlainTextResponse(Response): ...
class RedirectResponse(Response): ...
class StreamingResponse(Response): ...
class FileResponse(Response): ...

# Module for responses
class Responses:
    @staticmethod
    def get_json_response() -> type[JSONResponse]: ...
    @staticmethod
    def get_html_response() -> type[HTMLResponse]: ...
    @staticmethod
    def get_plaintext_response() -> type[PlainTextResponse]: ...
    @staticmethod
    def get_redirect_response() -> type[RedirectResponse]: ...
    @staticmethod
    def get_streaming_response() -> type[StreamingResponse]: ...
    @staticmethod
    def get_file_response() -> type[FileResponse]: ...
    @staticmethod
    def get_response() -> type[Response]: ...

# Make response classes available from responses submodule
responses: Responses
