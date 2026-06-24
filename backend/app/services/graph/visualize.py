"""
Render the LangGraph agent graph to a PNG file.

Usage (from backend/app):
    python -m services.graph.visualize
    python -m services.graph.visualize --output path/to/graph.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

from services.graph.graph import graph_builder

DEFAULT_OUTPUT = Path(__file__).resolve().parent / "graph.png"


def draw_graph_png(output_path: Path | str = DEFAULT_OUTPUT) -> Path:
    """Compile the agent graph and write a Mermaid PNG (via mermaid.ink)."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    graph = graph_builder()
    graph.get_graph().draw_mermaid_png(output_file_path=str(output))
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Export the chatbot LangGraph as PNG")
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output PNG path (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()

    path = draw_graph_png(args.output)
    print(f"Graph written to {path}")


if __name__ == "__main__":
    main()
