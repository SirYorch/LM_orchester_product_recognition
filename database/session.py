"""
Session Factory for Business Backend.

Provides async session management using SQLAlchemy 2.0.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.connection import get_engine
from logging_config import get_logger

logger = get_logger(__name__)


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Get async session factory.

    Returns:
        async_sessionmaker configured for the engine
    """
    logger.debug("Creating async session factory")
    engine = get_engine()
    factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    logger.debug("Async session factory created successfully")
    return factory


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions.

    Usage:
        async with get_session() as session:
            result = await session.execute(query)

    Yields:
        AsyncSession instance
    """
    logger.debug("Creating new database session")
    factory = get_session_factory()
    async with factory() as session:
        try:
            logger.debug("Database session opened")
            yield session
            logger.debug("Committing database transaction")
            await session.commit()
            logger.debug("Database transaction committed successfully")
        except Exception as e:
            logger.error(f"Database error occurred: {str(e)}")
            logger.debug("Rolling back database transaction")
            await session.rollback()
            raise
