from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables.config import RunnableConfig

from src.agent.state import AgentState, SummaryOutput
from src.llm.factory import get_llm
from src.llm.tracker import get_configured_callbacks
from src.prompts.system_prompts import SUMMARIZE_SYSTEM_PROMPT


def summarize_results(state: AgentState, config: RunnableConfig) -> dict:
    print("--- NODE: SUMMARIZING RESULTS ---")
    question = state.get("standalone_query", state.get("query"))
    raw_data = state.get("db_results")
    error = state.get("error")
    model_name = config.get("configurable", {}).get("model_name", "gpt-4o-mini")
    if error:
        failure_msg = (
            f"Sorry, I couldn't extract this data after several self-correction attempts. "
            f"Final technical error: {error}"
        )
        print("✗ Max retries failed. Returning error summary.\n")
        return {
            "summary": failure_msg,
            "chart_type": "none",
            "messages": [AIMessage(content=failure_msg)],
        }
    llm = get_llm(model_name=model_name)
    callbacks = get_configured_callbacks(config)
    structured_llm = llm.with_structured_output(SummaryOutput)
    messages = [
        SystemMessage(content=SUMMARIZE_SYSTEM_PROMPT),
        HumanMessage(content=f"Question: {question}\n\nRaw Data:\n{raw_data}"),
    ]
    response = structured_llm.invoke(messages, config={"callbacks": callbacks})
    print(f"✓ Summary generated. Chosen chart: {response.chart_type.upper()}\n")
    return {
        "summary": response.summary,
        "chart_type": response.chart_type,
        "messages": [AIMessage(content=response.summary)],
    }
