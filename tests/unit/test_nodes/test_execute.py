"""Unit tests for the execute_sql security guardrail and connector integration."""
import sqlite3
import threading
import time
from unittest.mock import MagicMock

import pytest

from src.agent.nodes.execute import _execute_with_timeout, execute_sql
from src.connectors.base import DatabaseConnector


def _config(connector=None):
    return {"configurable": {"connector": connector} if connector else {}}


def _mock_connector(cols=None, rows=None):
    """Return a mock DatabaseConnector with preset execute() return values."""
    connector = MagicMock(spec=DatabaseConnector)
    connector.execute.return_value = (
        cols or ["customer_id", "customer_city", "customer_state"],
        rows or [("c1", "sao paulo", "SP")],
    )
    return connector


class TestSecurityGuardrail:
    """Tests that only SELECT statements pass through; DDL/DML are blocked."""

    def test_select_passes_through(self):
        """A valid SELECT query should reach the DB layer (mocked) without security error."""
        state = {"sql_query": "SELECT * FROM customers", "retry_count": 0}
        connector = _mock_connector()
        result = execute_sql(state, _config(connector))
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
        connector = _mock_connector(cols=[], rows=[])
        connector.execute.return_value = ([], [])
        result = execute_sql(state, _config(connector))
        assert "Security Violation" not in result.get("error", "")

    def test_connector_error_is_captured(self):
        """Errors raised by the connector are caught and returned as error state."""
        state = {"sql_query": "SELECT * FROM missing", "retry_count": 0}
        connector = MagicMock(spec=DatabaseConnector)
        connector.execute.side_effect = Exception("no such table: missing")
        result = execute_sql(state, _config(connector))
        assert "no such table: missing" in result["error"]
        assert result["retry_count"] == 1


class TestExecuteWithTimeout:
    """Tests for the _execute_with_timeout helper."""

    def test_fast_query_returns_result(self):
        """A query completing well within the timeout returns normally."""
        connector = _mock_connector(cols=["id"], rows=[(1,)])
        cols, rows = _execute_with_timeout(connector, "SELECT 1", timeout=5.0)
        assert cols == ["id"]
        assert rows == [(1,)]

    def test_slow_connector_raises_timeout_error(self):
        """A connector that blocks longer than timeout raises TimeoutError."""
        connector = MagicMock(spec=DatabaseConnector)
        # No _conn attribute → no SQLite interrupt, uses threading fallback.
        del connector._conn

        def slow_execute(sql):
            time.sleep(10)
            return ([], [])

        connector.execute.side_effect = slow_execute
        with pytest.raises(TimeoutError):
            _execute_with_timeout(connector, "SELECT 1", timeout=0.1)

    def test_sqlite_interrupt_on_slow_query(self):
        """SQLite Connection.interrupt() is called when the deadline is reached."""
        # check_same_thread=False is required because the worker thread opens
        # a cursor on a connection created in the test (main) thread.
        conn = sqlite3.connect(":memory:", check_same_thread=False)
        connector = MagicMock(spec=DatabaseConnector)
        connector._conn = conn

        interrupted = threading.Event()

        def slow_execute(sql):
            cur = conn.cursor()
            # WITH RECURSIVE generates a huge result set; interrupt() will
            # abort it before completion.
            try:
                cur.execute(
                    "WITH RECURSIVE cnt(x) AS "
                    "(SELECT 1 UNION ALL SELECT x+1 FROM cnt WHERE x < 100000000) "
                    "SELECT x FROM cnt"
                )
                cur.fetchall()
            except sqlite3.OperationalError as exc:
                interrupted.set()
                raise exc

        connector.execute.side_effect = slow_execute

        with pytest.raises(TimeoutError):
            _execute_with_timeout(connector, "SELECT 1", timeout=0.5)

        assert interrupted.is_set(), "interrupt() should have fired"
        conn.close()

    def test_timeout_error_propagated_by_execute_sql(self):
        """execute_sql returns a timed-out error message when the query exceeds TIMEOUT_SECONDS."""
        state = {"sql_query": "SELECT 1", "retry_count": 0}
        connector = MagicMock(spec=DatabaseConnector)
        del connector._conn

        def slow_execute(sql):
            time.sleep(10)
            return ([], [])

        connector.execute.side_effect = slow_execute

        import src.agent.nodes.execute as execute_mod

        original = execute_mod.TIMEOUT_SECONDS
        execute_mod.TIMEOUT_SECONDS = 0.1
        try:
            result = execute_sql(state, _config(connector))
        finally:
            execute_mod.TIMEOUT_SECONDS = original

        assert "timed out" in result["error"].lower()
        assert result["retry_count"] == 1
