# API Documentation

Welcome to the CoachIQ API documentation. This documentation provides comprehensive information about the API endpoints, request/response formats, and data models.

## API Overview

The CoachIQ server provides a RESTful API for interacting with RV-C devices and systems. The API is organized into the following categories:

- [Entity API](/api/entities): Endpoints for managing and controlling entities (devices like lights, temperature sensors, etc.)
- [CAN Bus API](/api/can): Endpoints for interacting directly with the CAN bus
- [Configuration API](/api/config): Endpoints for retrieving and modifying system configuration
- [WebSocket API](/api/websocket): Real-time communication endpoints

## API Specification

The API is fully documented using the OpenAPI specification. You can:

- Browse the [OpenAPI Specification](/api/openapi) for details on how to use the API
- Access interactive API documentation at [http://localhost:8000/docs](http://localhost:8000/docs) when the server is running
- Use the raw OpenAPI schema to generate API clients for various programming languages

## Frontend Integration

The CoachIQ project includes a React frontend that consumes the API. For information about how the frontend integrates with the API, see the [Frontend API Integration](/api/frontend-integration) page.
