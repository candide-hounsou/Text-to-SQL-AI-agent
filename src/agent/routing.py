from langchain_core.runnables.config import RunnableConfig
from langgraph.graph import END

from src.agent.state import AgentState


def check_for_errors(state: AgentState, config: RunnableConfig) -> str:
    error = state.get("error")
    retries = state.get("retry_count", 0)
    configurable = config.get("configurable", {})
    use_self_correction = configurable.get("use_self_correction", True)
    if error:
        if not use_self_correction:
            print("--- ROUTING: SELF-CORRECTION DISABLED. FORCING END. ---")
            return "summarize_results"
        if retries >= 3:
            print(f"--- ROUTING: MAX RETRIES REACHED ({retries}/3). STOPPING LOOP. ---")
            return "summarize_results"
        else:
            print(f"--- ROUTING: ERROR DETECTED, RETRYING SQL GENERATION (Attempt {retries}/3) ---")
            return "generate_sql"
    else:
        print("--- ROUTING: SUCCESS, PROCEEDING TO SUMMARY ---")
        return "summarize_results"


def route_after_classification(state: AgentState, config: RunnableConfig) -> str:
    cat = state.get("query_complexity")
    safe_config = config or {}
    use_cot_planner = safe_config.get("configurable", {}).get("use_cot_planner", True)
    if cat == "out_of_scope":
        print("--- ROUTING: OUT OF SCOPE. ENDING. ---")
        return END
    elif cat == "complex":
        if use_cot_planner:
            print("--- ROUTING: COMPLEX QUERY. CoT PLANNER ENABLED. GOING TO PLANNER. ---")
            return "plan_sql_query"
        else:
            print("--- ROUTING: COMPLEX QUERY. CoT PLANNER DISABLED. GOING DIRECTLY TO SQL. ---")
            return "generate_sql"
    else:
        print("--- ROUTING: SIMPLE QUERY. GOING DIRECTLY TO SQL. ---")
        return "generate_sql"
