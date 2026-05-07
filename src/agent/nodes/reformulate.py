from langchain_core.messages import SystemMessage
from langchain_core.runnables.config import RunnableConfig

from src.agent.state import AgentState
from src.llm.factory import get_llm
from src.llm.tracker import get_configured_callbacks
from src.prompts.system_prompts import REFORMULATE_SYSTEM_PROMPT


def reformulate_query(state: AgentState, config: RunnableConfig) -> dict:
    print("--- NODE: REFORMULATING QUERY (CONTEXT MANAGEMENT) ---")
    query = state.get("query")
    messages = state.get("messages", [])
    model_name = config.get("configurable", {}).get("model_name", "gpt-4o-mini")
    if len(messages) <= 1:
        print("No history detected. Keeping original query.")
        return {"standalone_query": query}
    llm = get_llm(model_name=model_name)
    callbacks = get_configured_callbacks(config)
    history_text = "\n".join([f"{msg.type}: {msg.content}" for msg in messages[:-1]])
    system_prompt = REFORMULATE_SYSTEM_PROMPT.format(history_text=history_text, query=query)
    response = llm.invoke([SystemMessage(content=system_prompt)], config={"callbacks": callbacks})
    rewritten_query = response.content.strip()
    print(f"Original: {query}")
    print(f"Rewritten: {rewritten_query}\n")
    return {"standalone_query": rewritten_query}
