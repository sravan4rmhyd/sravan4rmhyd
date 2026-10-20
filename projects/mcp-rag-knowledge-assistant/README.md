# MCP RAG Knowledge Assistant

A Retrieval-Augmented Generation assistant exposed as an **MCP (Model Context Protocol) server**, so Claude Desktop,
Claude Code or any MCP client can query your documents with cited answers.

```
docs/*.md ─► paragraph-aware chunking ─► TF-IDF vector index ─► top-k retrieval ─► grounded answer + citations
                                                                      ▲
                               MCP tools: search_knowledge, ask_knowledge
```

## Features
- **Retrieval** with chunking and a vector index (`rag/index.py`). Runs fully offline; the `Retriever` is a small seam for swapping in an embedding model + vector DB (pgvector, Azure AI Search).
- **Grounded answers with citations** (`rag/answer.py`). Uses Claude when `ANTHROPIC_API_KEY` is set, otherwise an extractive answer. It refuses to answer when nothing relevant is retrieved.
- **MCP server** (`rag/server.py`) with two typed tools.
- **Offline evaluation** (`rag/evaluate.py`): recall@k and MRR over a labelled set, enforced in CI.

## Quick start
```bash
pip install -e ".[dev]"          # add ".[llm]" for LLM-generated answers
pytest -q
python -m rag.evaluate           # recall@3 / MRR
python -m rag.server             # stdio MCP server
```

Register with Claude Code:
```bash
claude mcp add knowledge -- python -m rag.server
```
Point it at your own corpus with `RAG_DOCS=/path/to/markdown`.
