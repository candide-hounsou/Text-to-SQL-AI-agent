import sqlite3
from typing import List, Tuple

from .base import DatabaseConnector


class SQLiteConnector(DatabaseConnector):
    """SQLite implementation of DatabaseConnector."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def connect(self) -> sqlite3.Connection:
        """Create a new connection for this thread.
        
        Creates a fresh connection each time to ensure thread-safety.
        SQLite connections can only be used in the thread they were created in.
        """
        return sqlite3.connect(self.db_path)

    def execute(self, query: str) -> Tuple[List[str], List[Tuple]]:
        """Execute query with a fresh, thread-local connection."""
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            column_names = [d[0] for d in cursor.description]
            rows = cursor.fetchmany(100)
            return column_names, rows
        finally:
            conn.close()

    def get_schema(self) -> str:
        """Get schema with a fresh, thread-local connection."""
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = cursor.fetchall()
            schema_parts = []
            for name, ddl in tables:
                if ddl:
                    schema_parts.append(ddl)
            return "\n\n".join(schema_parts)
        finally:
            conn.close()

    def close(self) -> None:
        """No-op since we don't cache connections anymore."""
        pass
