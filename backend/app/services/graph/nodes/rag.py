from langgraph.config import get_stream_writer
from langchain_core.runnables import RunnableConfig
from core.config import getSettings
from services.context_budget import apply_token_budget
from services.graph.state import AgentState
from services.graph.nodes.common import stream_completion
from services.rag import retrieve_context, to_sources, build_grounded_prompt


async def researcher(state: AgentState, config: RunnableConfig) -> dict:
    settings = getSettings()
    retrieved = await retrieve_context(
        embedding_service=config["configurable"]["embedding_service"],
        reranker_service=config["configurable"]["reranker_service"],
        vector_store=config["configurable"]["vector_store"],
        user_id=state["user_id"],
        message=state["user_message"],
        top_k=settings.RAG_TOP_K,
        document_ids=state["document_ids"],
    )
    return {
        "grounded_prompt": build_grounded_prompt(state["user_message"], retrieved),
        "sources": [s.model_dump(by_alias=True) for s in to_sources(retrieved)],
    }


async def writer(state: AgentState, config: RunnableConfig) -> dict:
    writer_fn = get_stream_writer()
    gemini = config["configurable"]["gemini"]
    prepared = await apply_token_budget(
        gemini=gemini,
        history=state["history"],
        prompt=state["grounded_prompt"],
        summary=state["context_summary"],
    )
    full = await stream_completion(
        gemini=gemini,
        writer=writer_fn,
        prompt=state["grounded_prompt"],
        prepared=prepared,
        sources=state["sources"],
    )
    return {"final_response": full}
