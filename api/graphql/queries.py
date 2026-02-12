"""
GraphQL queries for Business Backend.

This module exposes FAQs, Documents, and Products via GraphQL.
Products and images are read from PostgreSQL database.
"""

from typing import Annotated
from uuid import UUID

import strawberry
from aioinject import Inject
from aioinject.ext.strawberry import inject
from loguru import logger

from api.graphql.types import (
    FAQ,
    Document,
    ProductStockType,
    ProductSummaryType,
    SemanticSearchResponse,
    ProductImageType,
)
from services.product_service import ProductService
from services.search_service import SearchService


@strawberry.type
class BusinessQuery:
    """Business backend queries (FAQs, Documents, Products)."""

    # =====================
    # FAQs
    # =====================

    # @strawberry.field
    # @inject
    # async def get_faqs(
    #     self, tenant: str, data_service: Annotated[TenantDataService, Inject]
    # ) -> list[FAQ]:
    #     print(f"📋 GraphQL: getFaqs(tenant={tenant})")

    #     try:
    #         faq_data = await data_service.read_faqs_csv(tenant)
    #     except FileNotFoundError:
    #         return []

    #     faqs: list[FAQ] = []

    #     for item in faq_data.faq_items:
    #         faqs.append(
    #             FAQ(
    #                 type="faq",
    #                 patterns=item.patterns,
    #                 response=item.answer,
    #                 category=item.category,
    #             )
    #         )

    #     return faqs

    # =====================
    # Documents
    # =====================

    # @strawberry.field
    # @inject
    # async def get_documents(
    #     self, tenant: str, data_service: Annotated[TenantDataService, Inject]
    # ) -> list[Document]:
    #     print(f"📚 GraphQL: getDocuments(tenant={tenant})")

    #     try:
    #         chunks = await data_service.read_chunks_csv(tenant)
    #     except FileNotFoundError:
    #         return []

    #     return [
    #         Document(
    #             id=f"{tenant}_{idx}",
    #             title=chunk.category or "Unknown",
    #             content=chunk.content,
    #             category=chunk.category or "general",
    #         )
    #         for idx, chunk in enumerate(chunks)
    #     ]

    # =====================
    # Product Stock Queries
    # =====================

    @strawberry.field
    @inject
    async def products(
        self,
        product_service: Annotated[ProductService, Inject],
        limit: int = 50,
        offset: int = 0,
    ) -> list[ProductStockType]:
        print(f"📦 GraphQL: products(limit={limit}, offset={offset})")

        products = await product_service.list_products(limit=limit, offset=offset)

        result: list[ProductStockType] = []

        for p in products:
            images = await product_service.get_images_by_product_id(p.id)

            result.append(
                ProductStockType(
                    id=p.id,
                    created_at=p.created_at,
                    last_updated_at=p.last_updated_at,
                    product_id=p.product_id,
                    product_name=p.product_name,
                    product_sku=p.product_sku,
                    supplier_id=p.supplier_id,
                    supplier_name=p.supplier_name,
                    quantity_on_hand=p.quantity_on_hand,
                    quantity_reserved=p.quantity_reserved,
                    quantity_available=p.quantity_available,
                    minimum_stock_level=p.minimum_stock_level,
                    reorder_point=p.reorder_point,
                    optimal_stock_level=p.optimal_stock_level,
                    reorder_quantity=p.reorder_quantity,
                    average_daily_usage=p.average_daily_usage,
                    last_order_date=p.last_order_date,
                    last_stock_count_date=p.last_stock_count_date,
                    expiration_date=p.expiration_date,
                    unit_cost=p.unit_cost,
                    total_value=p.total_value,
                    batch_number=p.batch_number,
                    warehouse_location=p.warehouse_location,
                    shelf_location=p.shelf_location,
                    stock_status=p.stock_status,
                    is_active=p.is_active,
                    notes=p.notes,
                    images=[
                        ProductImageType(
                            image_type=img.image_type,
                            image_path=img.image_path,
                        )
                        for img in images
                    ],
                )
            )

        print(f"✅ GraphQL: Returned {len(result)} products")
        return result

    @strawberry.field
    @inject
    async def product(
        self,
        product_service: Annotated[ProductService, Inject],
        id: UUID,
    ) -> ProductStockType | None:
        print(f"📦 GraphQL: product(id={id})")

        p = await product_service.get_product(id)

        if p is None:
            return None

        images = await product_service.get_images_by_product_id(p.id)

        return ProductStockType(
            id=p.id,
            created_at=p.created_at,
            last_updated_at=p.last_updated_at,
            product_id=p.product_id,
            product_name=p.product_name,
            product_sku=p.product_sku,
            supplier_id=p.supplier_id,
            supplier_name=p.supplier_name,
            quantity_on_hand=p.quantity_on_hand,
            quantity_reserved=p.quantity_reserved,
            quantity_available=p.quantity_available,
            minimum_stock_level=p.minimum_stock_level,
            reorder_point=p.reorder_point,
            optimal_stock_level=p.optimal_stock_level,
            reorder_quantity=p.reorder_quantity,
            average_daily_usage=p.average_daily_usage,
            last_order_date=p.last_order_date,
            last_stock_count_date=p.last_stock_count_date,
            expiration_date=p.expiration_date,
            unit_cost=p.unit_cost,
            total_value=p.total_value,
            batch_number=p.batch_number,
            warehouse_location=p.warehouse_location,
            shelf_location=p.shelf_location,
            stock_status=p.stock_status,
            is_active=p.is_active,
            notes=p.notes,
            images=[
                ProductImageType(
                    image_type=img.image_type,
                    image_path=img.image_path,
                )
                for img in images
            ],
        )

    # =====================
    # Search (simple, NO IA)
    # =====================

    @strawberry.field
    @inject
    async def search_products(
        self,
        product_service: Annotated[ProductService, Inject],
        name: str,
        limit: int = 20,
    ) -> list[ProductSummaryType]:
        print(f"🔍 GraphQL: searchProducts(name={name})")

        products = await product_service.search_by_name(name=name, limit=limit)

        return [
            ProductSummaryType(
                id=p.id,
                product_name=p.product_name,
                product_sku=p.product_sku,
                supplier_name=p.supplier_name,
                quantity_available=p.quantity_available,
                stock_status=p.stock_status,
                unit_cost=p.unit_cost,
                warehouse_location=p.warehouse_location,
                is_active=p.is_active,
            )
            for p in products
        ]

    # =====================
    # Semantic Search (FUERA DE TU ALCANCE)
    # =====================

    @strawberry.field
    @inject
    async def semantic_search(
        self,
        search_service: Annotated[SearchService, Inject],
        query: str,
    ) -> SemanticSearchResponse:
        response = await search_service.semantic_search(query)

        return SemanticSearchResponse(
            answer=response.answer,
            products_found=[
                ProductSummaryType(
                    id=p.id,
                    product_name=p.product_name,
                    product_sku=p.product_sku,
                    supplier_name=p.supplier_name,
                    quantity_available=p.quantity_available,
                    stock_status=p.stock_status,
                    unit_cost=p.unit_cost,
                    warehouse_location=p.warehouse_location,
                    is_active=p.is_active,
                )
                for p in response.products_found
            ],
            query=response.query,
        )
