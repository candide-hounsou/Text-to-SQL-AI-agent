"""PostgreSQL database connector."""

from typing import Any

from src.connectors.base import DatabaseConnector


class PostgreSQLConnector(DatabaseConnector):
    """Connector for PostgreSQL databases via psycopg2."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        dbname: str = "",
        user: str = "",
        password: str = "",
    ) -> None:
        self.host = host
        self.port = port
        self.dbname = dbname
        self.user = user
        self.password = password

    def connect(self) -> Any:
        try:
            import psycopg2
        except ImportError as exc:
            raise RuntimeError(
                "psycopg2 is required for PostgreSQL connectivity. "
                "Install it with: pip install psycopg2-binary"
            ) from exc
        return psycopg2.connect(
            host=self.host,
            port=self.port,
            dbname=self.dbname,
            user=self.user,
            password=self.password,
        )

    def execute(self, query: str) -> list[dict]:
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            column_names = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(column_names, row)) for row in rows]
        finally:
            conn.close()

    def get_schema(self) -> str:
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
                """
            )
            tables = [row[0] for row in cursor.fetchall()]
            lines = []
            for table in tables:
                cursor.execute(
                    """
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = %s
                    ORDER BY ordinal_position;
                    """,
                    (table,),
                )
                col_defs = ", ".join(f"{col} {dtype}" for col, dtype in cursor.fetchall())
                lines.append(f"CREATE TABLE {table} ({col_defs});")
            return "\n".join(lines)
        finally:
            conn.close()
