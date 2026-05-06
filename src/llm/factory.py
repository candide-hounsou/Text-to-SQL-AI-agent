import os
from enum import Enum
from typing import Optional


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"


PROVIDER_MODELS = {
    LLMProvider.OPENAI: ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
    LLMProvider.ANTHROPIC: ["claude-3-5-haiku-20241022", "claude-sonnet-4-5"],
    LLMProvider.GEMINI: ["gemini-2.0-flash", "gemini-2.5-pro"],
}


def get_llm(provider: str = "openai", model_name: Optional[str] = None, temperature: float = 0):
    """Return a chat LLM for the given provider and model."""
    try:
        provider_enum = LLMProvider(provider)
    except ValueError:
        raise ValueError(
            f"Unsupported LLM provider: {provider!r}. "
            f"Supported: {[p.value for p in LLMProvider]}"
        )

    if model_name is None:
        model_name = PROVIDER_MODELS[provider_enum][0]

    if provider_enum == LLMProvider.OPENAI:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model_name, temperature=temperature)

    elif provider_enum == LLMProvider.ANTHROPIC:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("Missing ANTHROPIC_API_KEY. Set it in your .env file.")
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model_name, temperature=temperature)

    elif provider_enum == LLMProvider.GEMINI:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("Missing GOOGLE_API_KEY. Set it in your .env file.")
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=model_name, temperature=temperature)

    raise ValueError(f"Unsupported LLM provider: {provider!r}")
