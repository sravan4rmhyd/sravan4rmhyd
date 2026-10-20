import json

import pytest

from rag.answer import answer
from rag.evaluate import evaluate
from rag.index import Retriever, chunk_text


@pytest.fixture(scope="module")
def retriever():
    return Retriever.from_dir("docs")


def test_chunking_respects_limit_and_skips_headings():
    chunks = chunk_text("# Title\nalpha beta\ngamma delta\n\nepsilon", "x.md", max_chars=15)
    assert all(len(c.text) <= 15 for c in chunks)
    assert not any(c.text.startswith("#") for c in chunks)


def test_retrieval_quality_threshold(retriever):
    result = evaluate(retriever, json.load(open("tests/eval_set.json")), k=3)
    assert result["recall_at_k"] >= 0.8


def test_answer_has_citations(retriever, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    out = answer("What does MERGE do?", retriever.search("What does MERGE do?"))
    assert out["citations"] and out["citations"][0]["source"] == "delta-lake.md"


def test_unknown_question_says_dont_know():
    assert "don't know" in answer("zzzz", [])["answer"]
