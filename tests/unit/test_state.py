"""Unit tests for state Pydantic models and AgentState typing."""
import pytest
from pydantic import ValidationError

from src.agent.state import QueryClassification, SummaryOutput


class TestQueryClassification:
    def test_simple_complexity(self):
        obj = QueryClassification(complexity="simple", reason="Only one table needed.")
        assert obj.complexity == "simple"
        assert obj.reason == "Only one table needed."

    def test_complex_complexity(self):
        obj = QueryClassification(complexity="complex", reason="Requires 3 joins.")
        assert obj.complexity == "complex"

    def test_out_of_scope_complexity(self):
        obj = QueryClassification(complexity="out_of_scope", reason="Not related to schema.")
        assert obj.complexity == "out_of_scope"

    def test_invalid_complexity_raises(self):
        with pytest.raises(ValidationError):
            QueryClassification(complexity="unknown", reason="bad value")

    def test_missing_reason_raises(self):
        with pytest.raises(ValidationError):
            QueryClassification(complexity="simple")


class TestSummaryOutput:
    def test_bar_chart(self):
        obj = SummaryOutput(summary="Top categories by revenue.", chart_type="bar")
        assert obj.chart_type == "bar"

    def test_none_chart(self):
        obj = SummaryOutput(summary="There are 42 customers.", chart_type="none")
        assert obj.chart_type == "none"

    def test_valid_chart_types(self):
        for ct in ("bar", "line", "pie", "none"):
            obj = SummaryOutput(summary="some answer", chart_type=ct)
            assert obj.chart_type == ct

    def test_invalid_chart_type_raises(self):
        with pytest.raises(ValidationError):
            SummaryOutput(summary="some answer", chart_type="histogram")

    def test_missing_summary_raises(self):
        with pytest.raises(ValidationError):
            SummaryOutput(chart_type="bar")
