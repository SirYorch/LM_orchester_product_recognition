"""
Search Service for Business Backend.

Orchestrates LLM with product search tool for semantic queries.
"""

import logging
from dataclasses import dataclass

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from database.models import ProductStock
from llm.provider import LLMProvider
from llm.tools.product_search_tool import (
    ProductSearchTool,
    create_product_search_tool,
)
from services.product_service import ProductService
from logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class SearchResult:
    """Result from semantic search."""

    answer: str
    products_found: list[ProductStock]
    query: str


class SearchService:
    """Service for semantic search using LLM and product database."""

    SYSTEM_PROMPT = """You are a helpful inventory assistant. You help users find products and check stock availability.

When a user asks about products or stock, use the product_search tool to find information in the database.

Always provide clear, concise answers about:
- Whether the product exists
- How many units are available
- The product's stock status (In Stock, Low Stock, Out of Stock)
- Price and supplier information when relevant

If no products are found, let the user know politely and suggest they try a different search term.

Respond in the same language as the user's query."""

    def __init__(
        self,
        llm_provider: LLMProvider | None,
        product_service: ProductService,
    ) -> None:
        """
        Initialize SearchService.

        Args:
            llm_provider: LLM provider (can be None if disabled)
            product_service: ProductService for database queries
        """
        logger.debug("Initializing SearchService")
        self.llm_provider = llm_provider
        self.product_service = product_service
        self.search_tool: ProductSearchTool | None = None

        if llm_provider is not None:
            logger.debug("LLM provider configured, creating product search tool")
            self.search_tool = create_product_search_tool(product_service)
            logger.debug("Product search tool created successfully")
        else:
            logger.warning("LLM provider not configured, search will use fallback mode")
        
        logger.debug("SearchService initialized successfully")

    async def semantic_search(self, query: str) -> SearchResult:
        """
        Perform semantic search using LLM with product search tool.

        Args:
            query: User's natural language query

        Returns:
            SearchResult with answer and found products
        """
        logger.info(f"Starting semantic search for query: '{query}'")
        if self.llm_provider is None or self.search_tool is None:
            logger.warning("LLM not configured, using fallback search")
            return await self._fallback_search(query)

        try:
            logger.debug("Attempting LLM search with tool calling")
            result = await self._llm_search(query)
            logger.info(f"LLM search completed successfully, found {len(result.products_found)} products")
            return result
        except Exception as e:
            logger.error(f"LLM search failed: {str(e)}, falling back to direct search")
            return await self._fallback_search(query)

    async def _llm_search(self, query: str) -> SearchResult:
        """Perform search using LLM with tool calling."""
        logger.debug("Entering LLM search mode")
        assert self.llm_provider is not None
        assert self.search_tool is not None

        logger.debug("Binding tools to LLM model")
        model_with_tools = self.llm_provider.bind_tools([self.search_tool])

        logger.debug("Creating messages for LLM")
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ]

        logger.debug("First LLM invocation")
        response = await model_with_tools.ainvoke(messages)

        if hasattr(response, "tool_calls") and response.tool_calls:
            logger.info(f"LLM requested tool calls, executing {len(response.tool_calls)} tool(s)")
            tool_messages = []
            for tool_call in response.tool_calls:
                if tool_call["name"] == "product_search":
                    search_term = tool_call["args"]["search_term"]
                    logger.debug(f"Executing product_search tool with term: '{search_term}'")
                    tool_result = await self.search_tool._arun(search_term)
                    tool_messages.append(
                        ToolMessage(
                            content=tool_result,
                            tool_call_id=tool_call["id"],
                        )
                    )

            logger.debug("Second LLM invocation with tool results")
            messages_with_tools = [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": query},
                response,
                *tool_messages,
            ]

            final_response = await model_with_tools.ainvoke(messages_with_tools)
            answer = (
                final_response.content
                if isinstance(final_response.content, str)
                else str(final_response.content)
            )
        else:
            logger.debug("LLM did not request tool calls, using direct response")
            answer = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )

        result = SearchResult(
            answer=answer,
            products_found=self.search_tool.get_last_results(),
            query=query,
        )
        logger.debug("LLM search completed")
        return result

    async def _fallback_search(self, query: str) -> SearchResult:
        """
        Fallback search without LLM.

        Extracts keywords from query and searches directly.
        """
        logger.debug("Entering fallback search mode")
        search_term = query.strip()

        logger.debug(f"Extracting search term from query: '{query}'")
        for word in ["tienen", "hay", "existe", "buscar", "quiero", "stock", "?", "¿"]:
            search_term = search_term.lower().replace(word, "")
        search_term = search_term.strip()

        if not search_term:
            logger.warning("No search term extracted from query")
            return SearchResult(
                answer="Por favor, especifica el producto que buscas.",
                products_found=[],
                query=query,
            )

        logger.debug(f"Performing direct search with term: '{search_term}'")
        products = await self.product_service.search_by_name(search_term, limit=10)
        logger.info(f"Fallback search found {len(products)} product(s) for term '{search_term}'")

        if not products:
            answer = f"No encontré productos que coincidan con '{search_term}'."
        else:
            product_list = ", ".join(
                f"{p.product_name} ({p.quantity_available} disponibles)"
                for p in products[:5]
            )
            answer = f"Encontré {len(products)} producto(s): {product_list}"

        return SearchResult(
            answer=answer,
            products_found=products,
            query=query,
        )
