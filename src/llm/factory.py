from langchain_openai import ChatOpenAI


def get_llm(provider: str = "openai", model_name: str = "gpt-4o-mini", temperature: float = 0):
    """Return an LLM instance for the given provider and model.

    Currently only the "openai" provider is supported.
    """
    if provider == "openai":
        return ChatOpenAI(model=model_name, temperature=temperature)
    raise ValueError(f"Unsupported LLM provider: '{provider}'. Currently only 'openai' is supported.")
