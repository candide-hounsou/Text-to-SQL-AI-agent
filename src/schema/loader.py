import functools
import os


@functools.lru_cache(maxsize=1)
def get_schema() -> str:
    """Load the database schema from disk once and cache it in RAM."""
    print("⚙️ Loading schema into memory cache...")
    try:
        with open("data/schema.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Schema file not found."


def get_schema_for_query(
    query: str,
    index_path: str = "data/schema_index",
    use_rag: bool = True,
) -> str:
    """Return schema relevant to *query* using RAG when available.

    Falls back to the full schema when use_rag is False or the index is missing.
    """
    if use_rag and os.path.exists(index_path + ".pkl"):
        from src.schema.embedder import retrieve_relevant_schema
        return retrieve_relevant_schema(query, index_path=index_path)
    return get_schema()
