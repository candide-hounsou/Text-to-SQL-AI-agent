import os

from src.agent.graph import create_graph  # noqa: F401 – re-exported


def _require_openai_credentials() -> None:
    if os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_ADMIN_KEY"):
        return
    raise RuntimeError(
        "Missing OpenAI credentials. Set OPENAI_API_KEY in the project .env file "
        "or export OPENAI_API_KEY before starting the app."
    )


_require_openai_credentials()

__all__ = ["create_graph"]
