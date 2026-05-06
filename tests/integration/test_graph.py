"""Integration test for the full LangGraph agent graph with mocked LLM calls."""
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import HumanMessage

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_llm_mock(text_response: str = "SELECT 1"):
    """Return a mock ChatOpenAI that returns text_response on invoke()."""
    llm = MagicMock()
    response = MagicMock()
    response.content = text_response
    llm.invoke.return_value = response
    llm.with_structured_output.return_value = llm
    return llm


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _set_fake_api_key(monkeypatch):
    """Provide a fake API key so credential checks pass without a real key."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-fake-key-for-unit-tests")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGraphIntegration:
    def test_graph_compiles(self):
        """The create_graph() function should return a compiled graph without errors."""
        from src.agent.graph import create_graph
        graph = create_graph()
        assert graph is not None

    def test_out_of_scope_query_ends_early(self, monkeypatch):
        """An out-of-scope classification should end the graph without generating SQL."""
        from src.agent.graph import create_graph
        from src.agent.state import QueryClassification

        classification_result = QueryClassification(
            complexity="out_of_scope",
            reason="This question is not related to the e-commerce schema."
        )

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="What is the weather?")
        mock_llm.with_structured_output.return_value = MagicMock(
            invoke=MagicMock(return_value=classification_result)
        )

        with patch("src.agent.nodes.reformulate.get_llm", return_value=mock_llm), \
             patch("src.agent.nodes.classify.get_llm", return_value=mock_llm), \
             patch("src.agent.nodes.classify.get_schema", return_value="TABLE customers"), \
             patch("src.agent.nodes.reformulate.get_llm", return_value=mock_llm):
            graph = create_graph()
            state = {"query": "What is the weather?", "messages": [HumanMessage(content="What is the weather?")]}
            config = {"configurable": {"thread_id": "test-oos"}}
            final = graph.invoke(state, config=config)

        # Out-of-scope: no SQL should be generated
        assert final.get("sql_query") is None or final.get("sql_query") == ""

    def test_simple_query_produces_summary(self, monkeypatch):
        """A simple query with mocked LLM and DB should reach the summarize node."""
        from src.agent.graph import create_graph
        from src.agent.state import QueryClassification, SummaryOutput

        classification_result = QueryClassification(complexity="simple", reason="One table, basic filter.")
        summary_result = SummaryOutput(summary="There are 2 customers.", chart_type="none")

        # Standalone query reformulation mock
        reformulate_llm = MagicMock()
        reformulate_llm.invoke.return_value = MagicMock(content="How many customers are there?")

        # Classification mock
        classify_llm = MagicMock()
        classify_llm.with_structured_output.return_value = MagicMock(
            invoke=MagicMock(return_value=classification_result)
        )

        # SQL generation mock
        generate_llm = MagicMock()
        generate_llm.invoke.return_value = MagicMock(content="SELECT COUNT(*) FROM customers")

        # Summary mock
        summarize_llm = MagicMock()
        summarize_llm.with_structured_output.return_value = MagicMock(
            invoke=MagicMock(return_value=summary_result)
        )

        # Mock DB execution
        mock_cursor = MagicMock()
        mock_cursor.fetchmany.return_value = [(2,)]
        mock_cursor.description = [("COUNT(*)",)]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        with patch("src.agent.nodes.reformulate.get_llm", return_value=reformulate_llm), \
             patch("src.agent.nodes.classify.get_llm", return_value=classify_llm), \
             patch("src.agent.nodes.classify.get_schema", return_value="TABLE customers"), \
             patch("src.agent.nodes.generate.get_llm", return_value=generate_llm), \
             patch("src.agent.nodes.generate.get_schema_for_query", return_value="TABLE customers"), \
             patch("src.agent.nodes.summarize.get_llm", return_value=summarize_llm), \
             patch("src.connectors.sqlite.sqlite3.connect", return_value=mock_conn):
            graph = create_graph()
            state = {
                "query": "How many customers are there?",
                "messages": [HumanMessage(content="How many customers are there?")],
            }
            config = {"configurable": {"thread_id": "test-simple"}}
            final = graph.invoke(state, config=config)

        assert final.get("summary") == "There are 2 customers."
        assert final.get("chart_type") == "none"
