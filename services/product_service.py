"""
Product Service for Business Backend.

Provides CRUD operations for ProductStock using SQLAlchemy ORM.
"""

import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models import ProductStock
from logging_config import get_logger

logger = get_logger(__name__)


class ProductService:
    """Service for product stock operations."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        """
        Initialize ProductService.

        Args:
            session_factory: Async session factory for database operations
        """
        logger.debug("Initializing ProductService")
        self.session_factory = session_factory
        logger.debug("ProductService initialized successfully")

    async def list_products(
        self,
        limit: int = 50,
        offset: int = 0,
        active_only: bool = True,
    ) -> list[ProductStock]:
        """
        List products with pagination.

        Args:
            limit: Maximum number of products to return
            offset: Number of products to skip
            active_only: If True, only return active products

        Returns:
            List of ProductStock instances
        """
        logger.debug(f"Listing products with limit={limit}, offset={offset}, active_only={active_only}")
        try:
            async with self.session_factory() as session:
                query = select(ProductStock)

                if active_only:
                    query = query.where(ProductStock.is_active == True)  # noqa: E712

                query = query.order_by(ProductStock.product_name).limit(limit).offset(offset)

                result = await session.execute(query)
                products = list(result.scalars().all())
                logger.info(f"Retrieved {len(products)} products")
                return products
        except Exception as e:
            logger.error(f"Error listing products: {str(e)}")
            raise

    async def get_product(self, product_id: UUID) -> ProductStock | None:
        """
        Get a single product by ID.

        Args:
            product_id: UUID of the product

        Returns:
            ProductStock instance or None if not found
        """
        logger.debug(f"Retrieving product with ID: {product_id}")
        try:
            async with self.session_factory() as session:
                query = select(ProductStock).where(ProductStock.id == product_id)
                result = await session.execute(query)
                product = result.scalar_one_or_none()
                if product:
                    logger.info(f"Product found: {product.product_name}")
                else:
                    logger.warning(f"Product not found with ID: {product_id}")
                return product
        except Exception as e:
            logger.error(f"Error retrieving product {product_id}: {str(e)}")
            raise

    async def search_by_name(
        self,
        name: str,
        limit: int = 20,
        active_only: bool = True,
    ) -> list[ProductStock]:
        """
        Search products by name (case-insensitive).

        Args:
            name: Search term for product name
            limit: Maximum number of results
            active_only: If True, only return active products

        Returns:
            List of matching ProductStock instances
        """
        logger.debug(f"Searching products by name: '{name}', limit={limit}")
        try:
            async with self.session_factory() as session:
                query = select(ProductStock).where(
                    ProductStock.product_name.ilike(f"%{name}%")
                )

                if active_only:
                    query = query.where(ProductStock.is_active == True)  # noqa: E712

                query = query.order_by(ProductStock.product_name).limit(limit)

                result = await session.execute(query)
                products = list(result.scalars().all())
                logger.info(f"Found {len(products)} products matching '{name}'")
                return products
        except Exception as e:
            logger.error(f"Error searching products by name '{name}': {str(e)}")
            raise

    async def get_low_stock_products(self, limit: int = 50) -> list[ProductStock]:
        """
        Get products with stock below reorder point.

        Args:
            limit: Maximum number of results

        Returns:
            List of ProductStock instances with low stock
        """
        logger.debug(f"Retrieving low stock products, limit={limit}")
        try:
            async with self.session_factory() as session:
                query = (
                    select(ProductStock)
                    .where(ProductStock.is_active == True)  # noqa: E712
                    .where(ProductStock.quantity_available <= ProductStock.reorder_point)
                    .order_by(ProductStock.quantity_available)
                    .limit(limit)
                )

                result = await session.execute(query)
                products = list(result.scalars().all())
                logger.info(f"Found {len(products)} products with low stock")
                return products
        except Exception as e:
            logger.error(f"Error retrieving low stock products: {str(e)}")
            raise

    async def count_products(self, active_only: bool = True) -> int:
        """
        Count total products.

        Args:
            active_only: If True, only count active products

        Returns:
            Total count of products
        """
        logger.debug(f"Counting products, active_only={active_only}")
        try:
            async with self.session_factory() as session:
                query = select(func.count(ProductStock.id))

                if active_only:
                    query = query.where(ProductStock.is_active == True)  # noqa: E712

                result = await session.execute(query)
                count = result.scalar_one()
                logger.info(f"Total products count: {count}")
                return count
        except Exception as e:
            logger.error(f"Error counting products: {str(e)}")
            raise
