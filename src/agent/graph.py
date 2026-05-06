from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from src.agent.nodes import (
    classify_query,
    execute_sql,
    generate_sql,
    plan_sql_query,
    reformulate_query,
    summarize_results,
)
from src.agent.routing import check_for_errors, route_after_classification
from src.agent.state import AgentState


def create_graph():
    """Build and compile the LangGraph agent workflow."""
    memory = MemorySaver()
    workflow = StateGraph(AgentState)
    workflow.add_node("reformulate_query", reformulate_query)
    workflow.add_node("classify_query", classify_query)
    workflow.add_node("plan_sql_query", plan_sql_query)
    workflow.add_node("generate_sql", generate_sql)
    workflow.add_node("execute_sql", execute_sql)
    workflow.add_node("summarize_results", summarize_results)
    workflow.add_edge(START, "reformulate_query")
    workflow.add_edge("reformulate_query", "classify_query")
    workflow.add_conditional_edges(
        "classify_query",
        route_after_classification,
        {END: END, "plan_sql_query": "plan_sql_query", "generate_sql": "generate_sql"},
    )
    workflow.add_edge("plan_sql_query", "generate_sql")
    workflow.add_edge("generate_sql", "execute_sql")
    workflow.add_conditional_edges(
        "execute_sql",
        check_for_errors,
        {"generate_sql": "generate_sql", "summarize_results": "summarize_results"},
    )
    workflow.add_edge("summarize_results", END)
    return workflow.compile(checkpointer=memory)
