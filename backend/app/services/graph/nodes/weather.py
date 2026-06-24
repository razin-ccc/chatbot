import re

from langgraph.config import get_stream_writer
from pydantic import BaseModel
from langchain_core.runnables import RunnableConfig

from services.context_budget import apply_token_budget
from services.graph.state import AgentState
from services.weather import fetch_open_meteo

_CITY_PATTERNS = (
    re.compile(
        r"\b(?:weather|forecast|temperature|rain|humidity|wind|climate)\b"
        r"\s+(?:in|for|at)\s+"
        r"([A-Za-z][A-Za-z\s\-'.]{0,60}?)"
        r"(?:\?|$|\.|,|\s+(?:today|tomorrow|now|please))",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:in|for|at)\s+([A-Za-z][A-Za-z\s\-'.]{1,60}?)(?:\?|$|\.|,)",
        re.IGNORECASE,
    ),
)

CLARIFICATION = (
    "Which city would you like weather information for? "
    "For example: \"What's the weather in London?\""
)


def _extract_city(message: str) -> str | None:
    for pattern in _CITY_PATTERNS:
        match = pattern.search(message.strip())
        if match:
            city = match.group(1).strip().rstrip("?.,")
            if city and len(city) >= 2:
                return city
    return None


async def weather(state: AgentState, config: RunnableConfig) -> dict:
    writer = get_stream_writer()
    gemini = config["configurable"]["gemini"]

    prepared = await apply_token_budget(
        gemini=gemini,
        history=state["history"],
        prompt=state["user_message"],
        summary=state["context_summary"],
    )

    city = _extract_city(state["user_message"])
    if not city:
        writer({"event": "token", "content": CLARIFICATION})
        writer(
            {
                "event": "done",
                "prepared_messages": prepared.messages,
                "context_summary": prepared.summary,
            }
        )
        return {"final_response": CLARIFICATION}

    # Fetch weather
    try:
        weather_data = await fetch_open_meteo(city)
        weather_str = str(weather_data)
    except Exception:
        error_msg = (
            f"I couldn't find weather information for '{city}'. "
            "Please check the city name and try again."
        )
        writer({"event": "token", "content": error_msg})
        writer(
            {
                "event": "done",
                "prepared_messages": prepared.messages,
                "context_summary": prepared.summary,
            }
        )
        return {"final_response": error_msg}

    resolved_city = weather_data.get("city", city)
    chat_prompt = (
        f"The user asked: {state['user_message']}\n\n"
        f"Weather data for {resolved_city}:\n{weather_str}\n\n"
        "Provide a friendly, conversational answer using only this data."
    )

    full = ""
    async for chunk in gemini.chat(
        prompt=chat_prompt,
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
