"""Unit tests for routing functions."""
from langgraph.graph import END

from src.agent.routing import check_for_errors, route_after_classification


def _config(use_self_correction=True, use_cot_planner=True):
    return {"configurable": {"use_self_correction": use_self_correction, "use_cot_planner": use_cot_planner}}


class TestCheckForErrors:
    def test_no_error_goes_to_summarize(self):
        state = {"error": "", "retry_count": 0}
        result = check_for_errors(state, _config())
        assert result == "summarize_results"

    def test_error_first_retry(self):
        state = {"error": "SQLite Error: no such table", "retry_count": 0}
        result = check_for_errors(state, _config())
        assert result == "generate_sql"

    def test_error_second_retry(self):
        state = {"error": "SQLite Error: no such column", "retry_count": 2}
        result = check_for_errors(state, _config())
        assert result == "generate_sql"

    def test_max_retries_reached(self):
        state = {"error": "Some error", "retry_count": 3}
        result = check_for_errors(state, _config())
        assert result == "summarize_results"

    def test_self_correction_disabled(self):
        state = {"error": "Some error", "retry_count": 0}
        result = check_for_errors(state, _config(use_self_correction=False))
        assert result == "summarize_results"

    def test_no_error_key_goes_to_summarize(self):
        state = {}
        result = check_for_errors(state, _config())
        assert result == "summarize_results"


class TestRouteAfterClassification:
    def test_out_of_scope_ends(self):
        state = {"query_complexity": "out_of_scope"}
        result = route_after_classification(state, _config())
        assert result == END

    def test_complex_with_cot_goes_to_planner(self):
        state = {"query_complexity": "complex"}
        result = route_after_classification(state, _config(use_cot_planner=True))
        assert result == "plan_sql_query"

    def test_complex_without_cot_goes_to_generate(self):
        state = {"query_complexity": "complex"}
        result = route_after_classification(state, _config(use_cot_planner=False))
        assert result == "generate_sql"

    def test_simple_goes_to_generate(self):
        state = {"query_complexity": "simple"}
        result = route_after_classification(state, _config())
        assert result == "generate_sql"
