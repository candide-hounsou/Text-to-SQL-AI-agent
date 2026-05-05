import functools


@functools.lru_cache(maxsize=1)
def get_schema() -> str:
    """Load and cache the database schema from disk."""
    print("⚙️ Loading schema into memory cache...")
    try:
        with open("data/schema.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Schema file not found."
