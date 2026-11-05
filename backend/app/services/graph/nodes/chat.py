from langgraph.config import get_stream_writer
from langchain_core.runnables import RunnableConfig
from services.context_budget import apply_token_budget
from services.graph.state import AgentState
from services.graph.nodes.common import stream_completion


async def chat(state: AgentState, config: RunnableConfig) -> dict:
    writer = get_stream_writer()
    llm = config["configurable"]["llm"]
    prepared = await apply_token_budget(
        llm=llm,
        history=state["history"],
        prompt=state["user_message"],
        summary=state["context_summary"],
    )
    full = await stream_completion(
        llm=llm,
        writer=writer,
        prompt=state["user_message"],
        prepared=prepared,
    )
    return {"final_response": full}
