import sqlite3
import time

import sqlparse
from langchain_core.runnables.config import RunnableConfig

from src.agent.state import AgentState

TIMEOUT_SECONDS = 5.0


def execute_sql(state: AgentState, config: RunnableConfig) -> dict:
    print("--- NODE: EXECUTING SQL ---")
    sql_query = state.get("sql_query", "")
    parsed_statements = sqlparse.parse(sql_query)
    for statement in parsed_statements:
        if not statement.is_whitespace:
            raw_type = statement.get_type()
            if raw_type:
                stmt_type = raw_type.upper()
                if stmt_type != "SELECT":
                    security_error = (
                        f"Security Violation: '{stmt_type}' operation detected. "
                        "Only SELECT queries are strictly allowed."
                    )
                    print(f"🚨 ALERT: {security_error}")
                    current_retries = state.get("retry_count", 0)
                    return {"error": security_error, "retry_count": current_retries + 1}
    conn = None
    try:
        conn = sqlite3.connect("data/olist.db")
        cursor = conn.cursor()
        start_time = time.time()

        def progress_handler():
            if time.time() - start_time > TIMEOUT_SECONDS:
                return 1
            return 0

        conn.set_progress_handler(progress_handler, 10000)
        cursor.execute(sql_query)
        conn.set_progress_handler(None, 0)
        results = cursor.fetchmany(100)
        column_names = [description[0] for description in cursor.description]
        raw_data_list = [dict(zip(column_names, row)) for row in results]
        if not results:
            formatted_results = "No results found."
        else:
            formatted_results = f"Columns: {', '.join(column_names)}\nData:\n"
            llm_row_limit = 10
            for row in results[:llm_row_limit]:
                formatted_results += str(row) + "\n"
            if len(results) > llm_row_limit:
                hidden_rows = len(results) - llm_row_limit
                formatted_results += (
                    f"\n... (WARNING: {hidden_rows} additional rows were retrieved but hidden "
                    "from you to save tokens. You MUST mention to the user that this is a partial "
                    "view and they should look at the table/CSV for the full data.)\n"
                )
            max_chars = 3000
            if len(formatted_results) > max_chars:
                formatted_results = (
                    formatted_results[:max_chars] + "\n... [FATAL: DATA TRUNCATED DUE TO EXTREME LENGTH]"
                )
        print("✓ Execution successful. Data fetched.\n")
        current_retries = state.get("retry_count", 0)
        return {
            "db_results": formatted_results,
            "raw_data": raw_data_list,
            "error": "",
            "retry_count": current_retries,
        }
    except sqlite3.OperationalError as e:
        if "interrupted" in str(e):
            error_msg = (
                f"SQLite Error: Execution timed out after {TIMEOUT_SECONDS} seconds. "
                "Your query is too slow. Check for missing ON clauses in your JOINs (Cartesian products)."
            )
        else:
            error_msg = f"SQLite Error: {str(e)}"
        print(f"✗ Execution failed! {error_msg}\n")
        current_retries = state.get("retry_count", 0)
        return {"error": error_msg, "retry_count": current_retries + 1}
    except Exception as e:
        error_msg = f"System Error: {str(e)}"
        print(f"✗ Execution failed! {error_msg}\n")
        current_retries = state.get("retry_count", 0)
        return {"error": error_msg, "retry_count": current_retries + 1}
    finally:
        if conn:
            conn.close()
