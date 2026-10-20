"""Chunking + TF-IDF vector index. Runs fully offline; swap in an embedding model via `Retriever`."""
from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass(frozen=True)
class Chunk:
    source: str
    text: str


@dataclass(frozen=True)
class Hit:
    chunk: Chunk
    score: float


def chunk_text(text: str, source: str, max_chars: int = 400) -> list[Chunk]:
    """Paragraph-aware chunking: pack whole lines into chunks up to max_chars."""
    chunks, buf = [], ""
    for line in (l.strip() for l in text.splitlines()):
        if not line or line.startswith("#"):
            continue
        if buf and len(buf) + len(line) + 1 > max_chars:
            chunks.append(Chunk(source, buf))
            buf = ""
        buf = f"{buf} {line}".strip()
    if buf:
        chunks.append(Chunk(source, buf))
    return chunks


class Retriever:
    def __init__(self, chunks: list[Chunk]):
        if not chunks:
            raise ValueError("no chunks to index")
        self.chunks = chunks
        self._vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
        self._matrix = self._vec.fit_transform([c.text for c in chunks])

    @classmethod
    def from_dir(cls, path: str | Path) -> "Retriever":
        chunks: list[Chunk] = []
        for f in sorted(Path(path).glob("*.md")):
            chunks += chunk_text(f.read_text(), f.name)
        return cls(chunks)

    def search(self, query: str, k: int = 3) -> list[Hit]:
        scores = cosine_similarity(self._vec.transform([query]), self._matrix)[0]
        order = scores.argsort()[::-1][:k]
        return [Hit(self.chunks[i], float(scores[i])) for i in order if scores[i] > 0]
