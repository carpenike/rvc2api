"""
Contains custom FastAPI middleware for the rvc2api application.

Middleware functions in this module are used to intercept HTTP requests
for purposes such as logging, metrics collection, or request modification.
"""

import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware

from core_daemon.metrics import HTTP_LATENCY, HTTP_REQUESTS


async def prometheus_http_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """
    FastAPI middleware to record Prometheus metrics for HTTP requests.
    It measures the latency of each request and increments a counter for
    requests, labeled by method, endpoint, and status code.
    Args:
        request: The incoming FastAPI Request object.
        call_next: A function to call to process the request and get the response.
    Returns:
        The response object from the next handler in the chain.
    """
    start = time.perf_counter()
    response = await call_next(request)
    latency = time.perf_counter() - start
    path = request.url.path
    method = request.method
    status = response.status_code
    HTTP_REQUESTS.labels(method=method, endpoint=path, status_code=status).inc()
    HTTP_LATENCY.labels(method=method, endpoint=path).observe(latency)
    return response


def configure_cors(app):
    """
    Add CORS middleware to the FastAPI app for development and production.
    Allows React frontend and other clients to access the API.
    """
    origins = [
        "http://localhost:5173",  # Vite dev server
        "http://localhost:8000",  # Same-origin
        "http://localhost",
        "http://localhost:8080",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
