from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables.config import RunnableConfig

from src.agent.state import AgentState, QueryClassification
from src.llm.factory import get_llm
from src.llm.tracker import get_configured_callbacks
from src.prompts.system_prompts import CLASSIFY_SYSTEM_PROMPT
from src.schema.loader import get_schema


def classify_query(state: AgentState, config: RunnableConfig) -> dict:
    print("--- NODE: CLASSIFYING QUERY ---")
    query = state.get("standalone_query")
    model_name = config.get("configurable", {}).get("model_name", "gpt-4o-mini")
    schema = get_schema()
    llm = get_llm(model_name=model_name)
    callbacks = get_configured_callbacks(config)
    structured_llm = llm.with_structured_output(QueryClassification)
    system_prompt = CLASSIFY_SYSTEM_PROMPT.format(schema=schema)
    result = structured_llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Question: {query}")
    ], config={"callbacks": callbacks})
    print(f"Classification: {result.complexity.upper()} - {result.reason}\n")
    summary = result.reason if result.complexity == "out_of_scope" else ""
    messages_to_add = [AIMessage(content=summary)] if summary else []
    return {
        "query_complexity": result.complexity,
        "classification_reason": result.reason,
        "summary": summary,
        "messages": messages_to_add
    }
