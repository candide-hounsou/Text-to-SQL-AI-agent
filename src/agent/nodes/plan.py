from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables.config import RunnableConfig

from src.agent.state import AgentState
from src.llm.factory import get_llm
from src.prompts.system_prompts import PLAN_SYSTEM_PROMPT
from src.schema.loader import get_schema


def plan_sql_query(state: AgentState, config: RunnableConfig) -> dict:
    print("--- NODE: PLANNING COMPLEX SQL ---")
    query = state.get("standalone_query")
    model_name = config.get("configurable", {}).get("model_name", "gpt-4o-mini")
    schema = get_schema()
    llm = get_llm(model_name=model_name)
    system_prompt = PLAN_SYSTEM_PROMPT.format(schema=schema)
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Plan the SQL execution for this question: {query}")
    ])
    plan = response.content.strip()
    print("Plan generated.\n")
    return {"sql_plan": plan}
