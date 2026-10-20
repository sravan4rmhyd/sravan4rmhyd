"""Offline retrieval evaluation: recall@k and MRR over a labelled question set."""
import json
import sys

from rag.index import Retriever


def evaluate(retriever: Retriever, cases: list[dict], k: int = 3) -> dict:
    hits_at_k, rr = 0, 0.0
    for c in cases:
        sources = [h.chunk.source for h in retriever.search(c["question"], k)]
        if c["expected_source"] in sources:
            hits_at_k += 1
            rr += 1 / (sources.index(c["expected_source"]) + 1)
    n = len(cases)
    return {"recall_at_k": hits_at_k / n, "mrr": rr / n, "k": k, "n": n}


if __name__ == "__main__":
    docs = sys.argv[1] if len(sys.argv) > 1 else "docs"
    cases = json.load(open(sys.argv[2] if len(sys.argv) > 2 else "tests/eval_set.json"))
    print(json.dumps(evaluate(Retriever.from_dir(docs), cases), indent=2))
