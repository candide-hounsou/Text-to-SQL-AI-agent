from abc import ABC, abstractmethod
from typing import Any


class DatabaseConnector(ABC):
    """Abstract base class for database connectors."""

    @abstractmethod
    def connect(self) -> Any:
        """Return a connection object."""

    @abstractmethod
    def execute(self, query: str) -> list[dict]:
        """Execute a query and return rows as a list of dicts."""

    @abstractmethod
    def get_schema(self) -> str:
        """Return a string representation of the database schema."""
