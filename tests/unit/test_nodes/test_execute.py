"""Unit tests for the execute_sql security guardrail."""
from unittest.mock import MagicMock, patch

from src.agent.nodes.execute import execute_sql


def _config():
    return {"configurable": {}}


class TestSecurityGuardrail:
    """Tests that only SELECT statements pass through; DDL/DML are blocked."""

    def test_select_passes_through(self):
        """A valid SELECT query should reach the DB layer (mocked) without security error."""
        state = {"sql_query": "SELECT * FROM customers", "retry_count": 0}
        mock_cursor = MagicMock()
        mock_cursor.fetchmany.return_value = [("c1", "sao paulo", "SP")]
        mock_cursor.description = [("customer_id",), ("customer_city",), ("customer_state",)]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        with patch("src.agent.nodes.execute.sqlite3.connect", return_value=mock_conn):
            result = execute_sql(state, _config())
        assert result.get("error") == ""
        assert result.get("raw_data") is not None

    def test_drop_table_is_blocked(self):
        state = {"sql_query": "DROP TABLE customers", "retry_count": 0}
        result = execute_sql(state, _config())
        assert "Security Violation" in result["error"]
        assert "DROP" in result["error"]
        assert result["retry_count"] == 1

    def test_insert_is_blocked(self):
        state = {"sql_query": "INSERT INTO customers VALUES ('x', 'city', 'ST')", "retry_count": 0}
        result = execute_sql(state, _config())
        assert "Security Violation" in result["error"]
        assert result["retry_count"] == 1

    def test_update_is_blocked(self):
        state = {"sql_query": "UPDATE customers SET customer_city = 'x'", "retry_count": 0}
        result = execute_sql(state, _config())
        assert "Security Violation" in result["error"]
        assert result["retry_count"] == 1

    def test_delete_is_blocked(self):
        state = {"sql_query": "DELETE FROM customers", "retry_count": 1}
        result = execute_sql(state, _config())
        assert "Security Violation" in result["error"]
        assert result["retry_count"] == 2

    def test_multiple_statements_first_select_second_drop_blocked(self):
        """When a second statement is non-SELECT, it should be blocked."""
        sql = "SELECT 1; DROP TABLE customers;"
        state = {"sql_query": sql, "retry_count": 0}
        result = execute_sql(state, _config())
        assert "Security Violation" in result["error"]

    def test_empty_query_attempts_db(self):
        """An empty query has no statements, so it skips the guardrail and hits the DB."""
        state = {"sql_query": "", "retry_count": 0}
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchmany.return_value = []
        mock_cursor.description = []
        mock_conn.cursor.return_value = mock_cursor
        with patch("src.agent.nodes.execute.sqlite3.connect", return_value=mock_conn):
            # The behaviour after guardrail depends on sqlite3 — we just check no security error
            result = execute_sql(state, _config())
        assert "Security Violation" not in result.get("error", "")
