"""Unit tests for the generate_sql node prompt construction."""
from unittest.mock import MagicMock, patch

import pytest

from src.agent.nodes.generate import generate_sql
from src.prompts.few_shot import FEW_SHOT_EXAMPLES


def _config(**kwargs):
    defaults = {"model_name": "gpt-4o-mini", "use_few_shot": True}
    defaults.update(kwargs)
    return {"configurable": defaults}


@pytest.fixture
def mock_llm():
    """Return a mock LLM that records its invocation messages."""
    llm = MagicMock()
    response = MagicMock()
    response.content = "SELECT COUNT(*) FROM customers"
    llm.invoke.return_value = response
    return llm


class TestGenerateSqlPromptConstruction:
    def test_few_shot_included_by_default(self, mock_llm):
        state = {"standalone_query": "How many customers are there?", "error": "", "sql_plan": ""}
        with patch("src.agent.nodes.generate.get_llm", return_value=mock_llm), \
             patch("src.agent.nodes.generate.get_schema", return_value="TABLE customers"):
            result = generate_sql(state, _config(use_few_shot=True))
        assert result["sql_query"] == "SELECT COUNT(*) FROM customers"
        call_messages = mock_llm.invoke.call_args[0][0]
        system_content = call_messages[0].content
        assert FEW_SHOT_EXAMPLES.strip() in system_content

    def test_few_shot_excluded_when_disabled(self, mock_llm):
        state = {"standalone_query": "How many customers are there?", "error": "", "sql_plan": ""}
        with patch("src.agent.nodes.generate.get_llm", return_value=mock_llm), \
             patch("src.agent.nodes.generate.get_schema", return_value="TABLE customers"):
            generate_sql(state, _config(use_few_shot=False))
        call_messages = mock_llm.invoke.call_args[0][0]
        system_content = call_messages[0].content
        assert "FEW-SHOT EXAMPLES" not in system_content

    def test_error_appended_to_prompt(self, mock_llm):
        state = {
            "standalone_query": "Count customers",
            "error": "SQLite Error: no such table: customers",
            "sql_plan": "",
        }
        with patch("src.agent.nodes.generate.get_llm", return_value=mock_llm), \
             patch("src.agent.nodes.generate.get_schema", return_value="TABLE customers"):
            generate_sql(state, _config())
        call_messages = mock_llm.invoke.call_args[0][0]
        system_content = call_messages[0].content
        assert "WARNING" in system_content
        assert "no such table: customers" in system_content

    def test_plan_appended_to_prompt_when_present(self, mock_llm):
        state = {
            "standalone_query": "Top 5 categories by revenue",
            "error": "",
            "sql_plan": "Step 1: Join order_items with products ...",
        }
        with patch("src.agent.nodes.generate.get_llm", return_value=mock_llm), \
             patch("src.agent.nodes.generate.get_schema", return_value="TABLE products"):
            generate_sql(state, _config())
        call_messages = mock_llm.invoke.call_args[0][0]
        system_content = call_messages[0].content
        assert "Step 1: Join order_items with products" in system_content

    def test_schema_injected_into_prompt(self, mock_llm):
        schema = "CREATE TABLE my_table (id INTEGER PRIMARY KEY);"
        state = {"standalone_query": "Count rows", "error": "", "sql_plan": ""}
        with patch("src.agent.nodes.generate.get_llm", return_value=mock_llm), \
             patch("src.agent.nodes.generate.get_schema", return_value=schema):
            generate_sql(state, _config())
        call_messages = mock_llm.invoke.call_args[0][0]
        system_content = call_messages[0].content
        assert schema in system_content
