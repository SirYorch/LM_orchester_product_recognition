"""
Database Connection for Business Backend.

Single-tenant async engine using SQLAlchemy 2.0.
"""

import functools
import logging

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine as sa_create_async_engine
from sqlalchemy.pool import NullPool

from config import get_business_settings
from logging_config import get_logger

logger = get_logger(__name__)


def create_async_engine(database_url: str) -> AsyncEngine:
    """
    Create async SQLAlchemy engine.

    Args:
        database_url: PostgreSQL connection URL

    Returns:
        AsyncEngine instance
    """
    print("Creating async SQLAlchemy engine")
    engine = sa_create_async_engine(  
        database_url,
        poolclass=NullPool,
        echo=False,
    )
    print(f"Async engine created for URL: {str(database_url)[:50]}...")
    return engine


@functools.cache
def get_engine() -> AsyncEngine:
    """
    Get cached async engine using settings.

    Returns:
        Cached AsyncEngine instance
    """
    print("Retrieving cached async engine")
    settings = get_business_settings()
    print("Creating engine from settings")
    engine = create_async_engine(str(settings.pg_url))
    print("Cached async engine retrieved successfully")
    return engine
