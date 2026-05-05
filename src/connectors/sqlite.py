import sqlite3

from .base import DatabaseConnector


class SQLiteConnector(DatabaseConnector):
    """SQLite implementation of DatabaseConnector."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def execute(self, query: str) -> list[dict]:
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            column_names = [d[0] for d in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(column_names, row)) for row in rows]
        finally:
            conn.close()

    def get_schema(self) -> str:
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
