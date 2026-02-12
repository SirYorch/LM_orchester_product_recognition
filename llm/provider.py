"""
LLM Provider for Business Backend.

Simple OpenAI provider using LangChain for tool calling.
"""

import logging
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from config import get_business_settings
from logging_config import get_logger

logger = get_logger(__name__)


class LLMProvider:
    """Provider for LLM interactions using LangChain."""

    def __init__(self, model: BaseChatModel) -> None:
        """
        Initialize LLM Provider.

        Args:
            model: LangChain chat model instance
        """
        logger.debug("Initializing LLMProvider")
        self.model = model
        logger.info("LLMProvider initialized successfully")

    def get_model(self) -> BaseChatModel:
        """Get the underlying LangChain model."""
        return self.model

    def bind_tools(self, tools: list) -> BaseChatModel:
        """
        Bind tools to the model for function calling.

        Args:
            tools: List of LangChain tools

        Returns:
            Model with tools bound
        """
        logger.debug(f"Binding {len(tools)} tool(s) to model")
        model_with_tools = self.model.bind_tools(tools)
        logger.info(f"Successfully bound {len(tools)} tool(s) to model")
        return model_with_tools


def create_llm_provider() -> LLMProvider | None:
    """
    Create LLM provider from settings.

    Returns:
        LLMProvider instance or None if disabled/not configured
    """
    logger.debug("Creating LLM provider from settings")
    settings = get_business_settings()

    if not settings.llm_enabled:
        logger.warning("LLM is disabled in settings")
        return None

    if not settings.openai_api_key:
        logger.warning("OpenAI API key not configured")
        return None

    logger.info(f"Creating ChatOpenAI model: {settings.openai_model}")
    model = ChatOpenAI(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        max_tokens=settings.openai_max_tokens,
        temperature=0,
    )

    provider = LLMProvider(model)
    logger.info("LLM provider created successfully")
    return provider
