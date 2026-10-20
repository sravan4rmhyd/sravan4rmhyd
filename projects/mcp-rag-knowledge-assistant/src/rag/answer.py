"""Grounded answers with citations. Uses an LLM when ANTHROPIC_API_KEY is set, else an extractive answer."""
import os

from rag.index import Hit

PROMPT = (
    "Answer the question using ONLY the numbered context. Cite sources like [1]. "
    "If the context is insufficient, say you don't know.\n\nContext:\n{context}\n\nQuestion: {question}"
)


def format_context(hits: list[Hit]) -> str:
    return "\n".join(f"[{i}] ({h.chunk.source}) {h.chunk.text}" for i, h in enumerate(hits, 1))


def answer(question: str, hits: list[Hit]) -> dict:
    if not hits:
        return {"answer": "I don't know: no relevant documents found.", "citations": []}
    citations = [{"id": i, "source": h.chunk.source, "score": round(h.score, 3)} for i, h in enumerate(hits, 1)]
    if os.environ.get("ANTHROPIC_API_KEY"):
        import anthropic

        msg = anthropic.Anthropic().messages.create(
            model=os.environ.get("RAG_MODEL", "claude-sonnet-5-5"),
            max_tokens=500,
            messages=[{"role": "user", "content": PROMPT.format(context=format_context(hits), question=question)}],
        )
        text = msg.content[0].text
    else:
        text = f"{hits[0].chunk.text} [1]"
    return {"answer": text, "citations": citations}
