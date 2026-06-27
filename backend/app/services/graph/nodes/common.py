def emit_done(writer, prepared, *, sources=None) -> None:
    """Emit the optional sources event and the terminal done event."""
    if sources is not None:
        writer({"event": "sources", "sources": sources})
    writer(
        {
            "event": "done",
            "prepared_messages": prepared.messages,
            "context_summary": prepared.summary,
        }
    )


async def stream_completion(*, gemini, writer, prompt, prepared, sources=None) -> str:
    """Stream a Gemini completion, emitting token/sources/done events."""
    full = ""
    async for chunk in gemini.chat(
        prompt=prompt,
        history=prepared.messages,
        context_summary=prepared.summary,
    ):
        full += chunk
        writer({"event": "token", "content": chunk})

    emit_done(writer, prepared, sources=sources)
    return full
