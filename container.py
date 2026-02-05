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
from collections.abc import Iterable
from typing import Any, Optional

import aioinject
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.session import get_session_factory
from llm.provider import LLMProvider, create_llm_provider
from services.product_service import ProductService
from services.search_service import SearchService




async def create_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Factory function for database session factory.

    Returns:
        async_sessionmaker for creating database sessions
    """
    return get_session_factory()


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
    return ProductService(session_factory)


async def create_llm_provider_instance() -> LLMProvider:
    """
    Factory function for LLM provider.

    Returns:
        LLMProvider instance or None if disabled
    """
    return create_llm_provider()


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
    return SearchService(llm_provider, product_service)


def providers() -> Iterable[aioinject.Provider[Any]]:
    """
    Create and return all dependency injection providers for 

    Includes:
    - TenantDataService: Reads tenant data from CSV files
    - ProductService: CRUD operations for product_stocks
    - LLMProvider: OpenAI via LangChain (optional)
    - SearchService: Semantic search with LLM
    """
    providers_list: list[aioinject.Provider[Any]] = []

    # Database
    providers_list.append(aioinject.Singleton(create_session_factory))
    providers_list.append(aioinject.Singleton(create_product_service))

    # LLM (optional - can return None)
    providers_list.append(aioinject.Singleton(create_llm_provider_instance))
    providers_list.append(aioinject.Singleton(create_search_service))

    return providers_list


@functools.cache
def create_business_container() -> aioinject.Container:
    """
    Create and configure the business_backend DI container.

    This container is completely independent from the agent's container.

    Returns:
        Configured aioinject.Container instance
    """
    container = aioinject.Container()
    for provider in providers():
        container.register(provider)
    return container
