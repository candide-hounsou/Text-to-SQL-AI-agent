"""MySQL database connector."""

from typing import Any, List, Tuple

from src.connectors.base import DatabaseConnector


class MySQLConnector(DatabaseConnector):
    """Connector for MySQL / MariaDB databases via mysql-connector-python."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 3306,
        database: str = "",
        user: str = "",
        password: str = "",
    ) -> None:
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self._conn = None

    def connect(self) -> None:
        try:
            import mysql.connector
        except ImportError as exc:
            raise RuntimeError(
                "mysql-connector-python is required for MySQL connectivity. "
                "Install it with: pip install mysql-connector-python"
            ) from exc
        self._conn = mysql.connector.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password,
        )

    def execute(self, sql: str) -> Tuple[List[str], List[Tuple[Any, ...]]]:
        if self._conn is None:
            self.connect()
        cursor = self._conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchmany(100)
        cols = [desc[0] for desc in cursor.description]
        return cols, rows

    def get_schema(self) -> str:
        if self._conn is None:
            self.connect()
        cursor = self._conn.cursor()
        cursor.execute("SHOW TABLES;")
        tables = [row[0] for row in cursor.fetchall()]
        lines = []
        for table in tables:
            cursor.execute(f"DESCRIBE `{table}`;")
            col_defs = ", ".join(f"{row[0]} {row[1]}" for row in cursor.fetchall())
            lines.append(f"CREATE TABLE {table} ({col_defs});")
        return "\n".join(lines)

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
