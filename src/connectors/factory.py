"""Factory function for database connectors."""

from src.connectors.base import DatabaseConnector


def get_connector(db_type: str, **kwargs) -> DatabaseConnector:
    """Return the appropriate DatabaseConnector for *db_type*.

    Parameters
    ----------
    db_type:
        One of ``"sqlite"``, ``"postgresql"``, ``"mysql"``, ``"csv"``.
    **kwargs:
        Connection parameters forwarded to the connector constructor.
    """
    db_type = db_type.lower()

    if db_type == "sqlite":
        from src.connectors.sqlite import SQLiteConnector
        return SQLiteConnector(**kwargs)

    if db_type == "postgresql":
        from src.connectors.postgresql import PostgreSQLConnector
        return PostgreSQLConnector(**kwargs)

    if db_type == "mysql":
        from src.connectors.mysql import MySQLConnector
        return MySQLConnector(**kwargs)

    if db_type == "csv":
        from src.connectors.csv_connector import CSVConnector
        return CSVConnector(**kwargs)

    raise ValueError(
        f"Unsupported db_type: {db_type!r}. "
        "Supported types: 'sqlite', 'postgresql', 'mysql', 'csv'."
    )
