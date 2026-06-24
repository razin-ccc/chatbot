from langgraph.graph import StateGraph, START, END

from services.graph.state import AgentState
from services.graph.classifier import classifier
from services.graph.nodes.chat import chat
from services.graph.nodes.rag import researcher, writer
from services.graph.nodes.weather import weather
from services.graph.nodes.bug_report import bug_report


def graph_builder():
    g = StateGraph(AgentState)
    g.add_node("classifier", classifier)
    g.add_node("researcher", researcher)
    g.add_node("writer", writer)
    g.add_node("chat", chat)
    g.add_node("weather", weather)
    g.add_node("bug_report", bug_report)

    g.add_edge(START, "classifier")
    g.add_conditional_edges(
        "classifier",
        lambda state: state["route"],
        {"chat": "chat", "rag": "researcher", "weather": "weather", "bug_report": "bug_report"},
    )
    g.add_edge("researcher", "writer")
    g.add_edge("writer", END)
    g.add_edge("chat", END)
    g.add_edge("weather", END)
    g.add_edge("bug_report", END)
    return g.compile()
