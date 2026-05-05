from operator import add
from typing import Annotated, List, Literal, TypedDict

from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field


class AgentState(TypedDict, total=False):
    query: str
    standalone_query: str
    query_complexity: Literal["simple", "complex", "out_of_scope"]
    classification_reason: str
    sql_plan: str
    sql_query: str
    db_results: str
    raw_data: list
    error: str
    retry_count: int
    summary: str
    chart_type: str
    messages: Annotated[List[BaseMessage], add]


class QueryClassification(BaseModel):
    complexity: Literal["simple", "complex", "out_of_scope"] = Field(
        description=(
            "Categorize the query. 'out_of_scope' if it cannot be answered by the schema. "
            "'simple' if it requires 1-2 tables and basic filtering. "
            "'complex' if it requires 3+ tables, advanced math, or complex aggregations."
        )
    )
    reason: str = Field(description="Explain why this category was chosen.")


class SummaryOutput(BaseModel):
    summary: str = Field(description="The natural language summary of the data.")
    chart_type: Literal["bar", "line", "pie", "none"] = Field(
        description=(
            "The best chart type to visualize this data. Use 'bar' for comparisons, "
            "'line' for time series/trends, 'pie' for proportions, and 'none' if it's a "
            "single number or unchartable."
        )
    )
