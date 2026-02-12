"""
Business Backend - Independent FastAPI Application.

This service provides GraphQL API for FAQs and Documents from CSV files.
Runs independently on port 9000 (configurable).

Architecture:
- Reads tenant data from CSV files (business_backend/data/{tenant}/)
- Exposes data via GraphQL queries (getFaqs, getDocuments)
- Completely independent from agent service
- No database access - stateless data provider

Usage:
    poetry run python -m main --port 9000
"""

import argparse
import logging

import strawberry

import uvicorn
from aioinject.ext.strawberry import AioInjectExtension
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter

from api.graphql.queries import BusinessQuery
from api.rest.routes2 import router as product_router
from container import create_business_container
from logging_config import configure_logging

logger = configure_logging(logging.INFO)


def create_business_backend_app() -> FastAPI:
    """
    Create independent FastAPI application for Business Backend.

    Returns:
        FastAPI application with GraphQL endpoint
    """
    print("Creating Business Backend FastAPI application")
    
    app = FastAPI(
        title="Business Backend API",
        description="Provides FAQs and Documents from CSV files via GraphQL",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    print("Configuring CORS middleware")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    print("Creating Business Backend DI container")
    container = create_business_container()
    print("Business Backend DI container created successfully")

    print("Creating GraphQL schema")
    schema = strawberry.Schema(
        query=BusinessQuery,
        extensions=[
            AioInjectExtension(container),
        ],
    )
    print("Business Backend GraphQL schema created successfully")

    print("Registering GraphQL router")
    graphql_app = GraphQLRouter(
        schema,
        graphiql=True,
    )
    app.include_router(graphql_app, prefix="/graphql")

    print("Registering product recognition router")
    app.include_router(product_router)

    @app.get("/health")
    async def health():
        """Health check for business backend service."""
        print("Health check endpoint called")
        return {
            "status": "ok",
            "service": "business_backend",
            "version": "1.0.0",
        }

    @app.get("/")
    async def root():
        """Root endpoint with service information."""
        print("Root endpoint called")
        return {
            "service": "Business Backend API",
            "version": "1.0.0",
            "graphql_endpoint": "/graphql",
            "graphiql_ui": "/graphql (browser)",
            "product_recognition_endpoints": ["/register", "/predict", "/preview_keypoints"],
            "health_check": "/health",
            "docs": "/docs",
        }

    print("Business Backend FastAPI app created successfully")
    return app


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Business Backend Service")
    _ = parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port to run business backend on (default: 9000)",
    )
    _ = parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )

    args = parser.parse_args()
    print("Command line arguments parsed successfully")

    app = create_business_backend_app()

    host: str = args.host
    port: int = args.port

    print(f"Starting Business Backend on {host}:{port}")
    print(f"GraphiQL UI available at http://localhost:{port}/graphql")
    print(f"API documentation available at http://localhost:{port}/docs")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
    )
