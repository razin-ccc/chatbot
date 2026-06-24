from langgraph.config import get_stream_writer
from langchain_core.runnables import RunnableConfig
from services.context_budget import apply_token_budget
from services.graph.state import AgentState


async def chat(state: AgentState, config: RunnableConfig) -> dict:
    writer = get_stream_writer()
    gemini = config["configurable"]["gemini"]
    prepared = await apply_token_budget(
        gemini=gemini,
        history=state["history"],
        prompt=state["user_message"],
        summary=state["context_summary"],
    )
    full = ""
    async for chunk in gemini.chat(
        prompt=state["user_message"],
        history=prepared.messages,
        context_summary=prepared.summary,
    ):
        full += chunk
        writer({"event": "token", "content": chunk})

    writer(
        {
            "event": "done",
            "prepared_messages": prepared.messages,
            "context_summary": prepared.summary,
        }
    )
    return {"final_response": full}
