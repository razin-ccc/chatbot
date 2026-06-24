from typing import Literal, TypedDict

Route = Literal["chat", "rag", "weather", "bug_report"]


class AgentState(TypedDict):
    user_id: str
    conversation_id: str
    user_message: str
    has_documents: bool
    document_ids: list[str]
    document_filenames: list[str]
    history: list
    context_summary: str | None
    route: Route
    route_reason: str
    grounded_prompt: str | None
    sources: list | None
    final_response: str | None
