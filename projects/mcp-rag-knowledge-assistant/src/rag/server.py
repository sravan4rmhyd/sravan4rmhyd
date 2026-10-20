"""MCP server exposing the knowledge base to any MCP client (Claude Desktop, Claude Code, ...)."""
import os

from mcp.server.fastmcp import FastMCP

from rag.answer import answer
from rag.index import Retriever

mcp = FastMCP("knowledge-assistant")
_retriever = Retriever.from_dir(os.environ.get("RAG_DOCS", "docs"))


@mcp.tool()
def search_knowledge(query: str, k: int = 3) -> list[dict]:
    """Return the top-k most relevant knowledge-base passages for a query."""
    k = max(1, min(k, 10))
    return [{"source": h.chunk.source, "score": round(h.score, 3), "text": h.chunk.text} for h in _retriever.search(query, k)]


@mcp.tool()
def ask_knowledge(question: str) -> dict:
    """Answer a question grounded in the knowledge base, with citations."""
    return answer(question, _retriever.search(question, 3))


if __name__ == "__main__":
    mcp.run()
