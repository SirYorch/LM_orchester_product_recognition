"""
Dependency Injection Container for Business Backend.

This container manages services for the business_backend system,
which is independent from the agent's container.

The business_backend is responsible for:
- Reading tenant data from CSV files
- Exposing data via GraphQL API
- Database access for product_stocks table
- LLM integration for semantic search (optional)
"""

import functools
import logging
from collections.abc import Iterable
from typing import Any, Optional

import aioinject
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.session import get_session_factory
from llm.provider import LLMProvider, create_llm_provider
from services.product_service import ProductService
from services.search_service import SearchService
from logging_config import get_logger

logger = get_logger(__name__)




async def create_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Factory function for database session factory.

    Returns:
        async_sessionmaker for creating database sessions
    """
    logger.debug("Creating database session factory")
    factory = get_session_factory()
    logger.info("Database session factory created successfully")
    return factory


async def create_product_service(
    session_factory: async_sessionmaker[AsyncSession],
) -> ProductService:
    """
    Factory function for ProductService.

    Args:
        session_factory: Database session factory

    Returns:
        ProductService instance
    """
    logger.debug("Creating ProductService instance")
    service = ProductService(session_factory)
    logger.info("ProductService instance created successfully")
    return service


async def create_llm_provider_instance() -> LLMProvider:
    """
    Factory function for LLM provider.

    Returns:
        LLMProvider instance or None if disabled
    """
    logger.debug("Creating LLM provider instance")
    provider = create_llm_provider()
    if provider:
        logger.info("LLM provider instance created successfully")
    else:
        logger.warning("LLM provider is disabled or not configured")
    return provider


async def create_search_service(
    llm_provider: LLMProvider,
    product_service: ProductService,
) -> SearchService:
    """
    Factory function for SearchService.

    Args:
        llm_provider: LLM provider (can be None)
        product_service: ProductService for database queries

    Returns:
        SearchService instance
    """
    logger.debug("Creating SearchService instance")
    service = SearchService(llm_provider, product_service)
    logger.info("SearchService instance created successfully")
    return service


def providers() -> Iterable[aioinject.Provider[Any]]:
    """
    Create and return all dependency injection providers.

    Includes:
    - TenantDataService: Reads tenant data from CSV files
    - ProductService: CRUD operations for product_stocks
    - LLMProvider: OpenAI via LangChain (optional)
    - SearchService: Semantic search with LLM
    """
    logger.debug("Creating dependency injection providers")
    providers_list: list[aioinject.Provider[Any]] = []

    logger.debug("Registering database providers")
    providers_list.append(aioinject.Singleton(create_session_factory))
    providers_list.append(aioinject.Singleton(create_product_service))

    logger.debug("Registering LLM and search providers")
    providers_list.append(aioinject.Singleton(create_llm_provider_instance))
    providers_list.append(aioinject.Singleton(create_search_service))

    logger.info(f"Dependency injection providers created successfully - total: {len(providers_list)}")
    return providers_list


@functools.cache
def create_business_container() -> aioinject.Container:
    """
    Create and configure the business_backend DI container.

    This container is completely independent from the agent's container.

    Returns:
        Configured aioinject.Container instance
    """
    logger.info("Creating business backend dependency injection container")
    container = aioinject.Container()
    
    logger.debug("Registering providers in container")
    for idx, provider in enumerate(providers(), 1):
        container.register(provider)
        logger.debug(f"Registered provider {idx}")
    
    logger.info("Business backend container created and configured successfully")
    return container
