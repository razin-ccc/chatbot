import re
from typing import Literal
from pydantic import BaseModel
from services.graph.state import AgentState, Route
from langchain_core.runnables import RunnableConfig

WEATHER_PATTERNS = [
    r"\bweather\b",
    r"\bforecast\b",
    r"\btemperature\b",
    r"\brain\b",
    r"\bhumidity\b",
    r"\bwind\b",
    r"\bwill it rain\b",
    r"\bhow hot\b",
    r"\bhow cold\b",
    r"\bclimate\b",
    r"\bdegrees?\b",
    r"\bcelcius\b",
    r"\bfahrenheit\b",
    r"\bsunny\b",
    r"\bcloudy\b",
    r"\bovercast\b",
    r"\bprecipitation\b",
    r"\bsnow\b",
    r"\bstorm\b",
    r"\btyphoon\b",
    r"\buv index\b",
    r"\bfeels like\b",
    r"\bweather in\b",
    r"\bforecast for\b",
    r"\btemperature in\b",
    r"\brain in\b",
]

BUG_PATTERNS = [
    r"\bbug\b",
    r"\bbroken\b",
    r"\berror\b",
    r"\bnot working\b",
    r"\bissue\b",
    r"\bcrashes\b",
    r"\bfailing\b"
]

RAG_PATTERNS = [
    r"\b(document|file|pdf|upload|attached)\b",
    r"\bbased on\b",
    r"\baccording to\b",
    r"\bin the (doc|document|file|upload)\b",
    r"\bfrom (my|the) (doc|document|file)\b",
    r"\bsummarize\b",
    r"\bsummary\b",
    r"\banalyze\b",
    r"\banalysis\b",
    r"\brefer\b",
    r"\bcite\b",
    r"\bquote\b",
    r"\bwhat does (it|the doc|the document|the file)\b",
    r"\bfind in\b",
    r"\bsearch\b",
    r"\bextract\b",
    r"\bpage \d+\b",
    r"\bread (the|my) (doc|document|file)\b",
]


def rule_based_route(message: str, has_documents: bool) -> Route | None:
    message_lower = message.lower().strip()

    if any(re.search(p, message_lower) for p in WEATHER_PATTERNS):
        return "weather"
    if any(re.search(p, message_lower) for p in BUG_PATTERNS):
        return "bug_report"
    if has_documents and any(re.search(p, message_lower) for p in RAG_PATTERNS):
        return "rag"
    return None


class RouteDecision(BaseModel):
    route: Literal["chat", "rag", "weather", "bug_report"]
    reason: str


async def classifier(state: AgentState, config: RunnableConfig) -> dict:
    message = state.get("user_message", "")
    has_docs = state.get("has_documents", False)

    #  Rule-based fast path (rule_based_route only returns "rag" when has_docs is True)
    route = rule_based_route(message, has_docs)
    if route:
        return {"route": route, "route_reason": f"Matched rule for {route}"}

    #  LLM structured classification
    gemini = config["configurable"]["gemini"]
    document_filenames = state.get("document_filenames", [])
    filenames_str = ", ".join(document_filenames) if document_filenames else "None"

    system_prompt = f"""
You are an intelligent router. Classify the user's intent into one of four routes: 'chat', 'rag', 'weather', or 'bug_report'.
The user currently has_uploaded_documents: {has_docs}.
If they have uploaded documents, the filenames are: {filenames_str}.
Rules:
- If the user asks about the weather, route to 'weather'.
- If the user is complaining that the app or a feature is broken,having trouble, throwing an error, or not working as expected, route to 'bug_report'.
- If the user asks a question that requires searching the uploaded documents, route to 'rag'.
- If the user just wants to chat, route to 'chat'.
- If route is 'rag' but has_uploaded_documents is False, fallback to 'chat'.
"""

    decision: RouteDecision = await gemini.classify_json(
        system_prompt=system_prompt, user_prompt=message, schema=RouteDecision
    )

    final_route = decision.route
    final_reason = decision.reason

    #  Hard guards
    if final_route == "rag" and not has_docs:
        final_route = "chat"
        final_reason = "No indexed documents; falling back to chat."

    return {"route": final_route, "route_reason": final_reason}
