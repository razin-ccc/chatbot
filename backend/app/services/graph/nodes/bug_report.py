from uuid import UUID

from pydantic import BaseModel
from langgraph.config import get_stream_writer
from langchain_core.runnables import RunnableConfig
from services.graph.state import AgentState
from schemas.models import PendingJiraTicket
from core.config import getSettings
from core.database import SessionLocal
from core.logging import logger


class BugReportInfo(BaseModel):
    title: str
    description: str


def _format_bug_context(state: AgentState) -> str:
    """Build extraction input from summary, recent turns, and the latest message."""
    sections: list[str] = []

    summary = state.get("context_summary")
    if summary:
        sections.append(f"Conversation summary:\n{summary}")

    history = state.get("history") or []
    if history:
        recent_turns = history[-6:]
        turn_lines = []
        for message in recent_turns:
            role = "User" if message.role == "user" else "Assistant"
            turn_lines.append(f"{role}: {message.content}")
        sections.append("Recent conversation:\n" + "\n".join(turn_lines))

    sections.append(f"Latest message:\n{state['user_message']}")
    return "\n\n".join(sections)


def _rate_limit_message(remaining_seconds: int | None) -> str:
    base = (
        "You have already submitted a bug report recently. "
        "Please wait before submitting another one to prevent spam."
    )
    if remaining_seconds is None:
        return base
    minutes = max(1, (remaining_seconds + 59) // 60)
    return f"{base} You can try again in about {minutes} minute(s)."


async def bug_report(state: AgentState, config: RunnableConfig) -> dict:
    writer = get_stream_writer()
    gemini = config["configurable"]["gemini"]
    memory_service = config["configurable"]["memory_service"]
    settings = getSettings()

    user_id = state["user_id"]
    conversation_id = state["conversation_id"]
    rate_limit_seconds = settings.BUG_REPORT_RATE_LIMIT_SECONDS

    acquired = await memory_service.try_acquire_rate_limit(
        user_id, action="bug_report", limit_seconds=rate_limit_seconds
    )
    if not acquired:
        ttl = await memory_service.get_rate_limit_ttl(user_id, action="bug_report")
        final_message = _rate_limit_message(ttl)
        writer({"event": "token", "content": final_message})
        writer({"event": "done"})
        return {"final_response": final_message}

    system_prompt = """
You are a technical support agent. The user is reporting a bug or issue with the application.
Based on the conversation summary, recent turns, and latest message, extract a concise title and a detailed description for a Jira ticket.
Include steps to reproduce when they were mentioned.
    """

    try:
        bug_info: BugReportInfo = await gemini.classify_json(
            system_prompt=system_prompt,
            user_prompt=_format_bug_context(state),
            schema=BugReportInfo,
        )

        writer(
            {
                "event": "token",
                "content": f"*[Drafting bug report: '{bug_info.title}']*\n\n",
            }
        )

        async with SessionLocal() as db:
            pending_ticket = PendingJiraTicket(
                user_id=UUID(user_id) if isinstance(user_id, str) else user_id,
                conversation_id=(
                    UUID(conversation_id)
                    if isinstance(conversation_id, str)
                    else conversation_id
                ),
                title=bug_info.title,
                description=bug_info.description,
                status="pending",
            )
            db.add(pending_ticket)
            await db.commit()

        final_message = (
            "I've drafted a bug report for our engineering team. "
            "An administrator will review and approve it shortly. "
            "You will receive an email once it is approved!"
        )
    except Exception as e:
        await memory_service.release_rate_limit(user_id, action="bug_report")
        logger.error(f"Failed to draft bug report: {e}")
        final_message = (
            "I'm sorry, you seem to be experiencing a bug, but I was unable to "
            "draft a bug report due to a system error. Please contact support."
        )

    writer({"event": "token", "content": final_message})
    writer({"event": "done"})

    return {"final_response": final_message}
