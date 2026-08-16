"""Knowledge index: loads a directory of markdown docs, chunks them by
heading, and serves ranked keyword search over the chunks.

Deliberately dependency-free (no embeddings service required) so the server
runs anywhere. Ranking is TF-IDF-weighted keyword overlap with a title boost —
simple, inspectable, and easily swapped for embeddings later (see README).
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

_WORD_RE = re.compile(r"[a-zA-Z0-9_]+")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")

# Words too common to carry signal in ranking.
_STOPWORDS = frozenset(
    """a an and are as at be by for from has have how in is it its of on or
    that the this to was we what when where which who will with you your""".split()
)


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _WORD_RE.findall(text) if t.lower() not in _STOPWORDS]


@dataclass
class Chunk:
    doc_path: str          # path relative to the docs root
    doc_title: str         # first H1 of the file, or the filename
    section: str           # heading path, e.g. "Escalation > Severity levels"
    text: str
    tokens: Counter = field(default_factory=Counter)

    @property
    def ref(self) -> str:
        """Stable reference a client can use to fetch this chunk again."""
        return f"{self.doc_path}#{self.section}" if self.section else self.doc_path


class KnowledgeIndex:
    def __init__(self) -> None:
        self.chunks: list[Chunk] = []
        self._df: Counter = Counter()          # document frequency per token
        self._by_doc: dict[str, list[int]] = defaultdict(list)

    # ------------------------------------------------------------------ load

    def load_directory(self, root: str | Path) -> int:
        """Index every .md file under `root`. Returns number of chunks."""
        root = Path(root)
        if not root.is_dir():
            raise FileNotFoundError(f"docs root not found: {root}")

        for path in sorted(root.rglob("*.md")):
            rel = path.relative_to(root).as_posix()
            self._index_file(rel, path.read_text(encoding="utf-8", errors="replace"))

        self._rebuild_df()
        return len(self.chunks)

    def _index_file(self, rel_path: str, content: str) -> None:
        doc_title = Path(rel_path).stem.replace("-", " ").replace("_", " ").title()
        heading_stack: list[str] = []
        buf: list[str] = []

        def flush() -> None:
            text = "\n".join(buf).strip()
            buf.clear()
            if not text:
                return
            section = " > ".join(heading_stack)
            chunk = Chunk(rel_path, doc_title, section, text)
            chunk.tokens = Counter(_tokenize(section + " " + text))
            self._by_doc[rel_path].append(len(self.chunks))
            self.chunks.append(chunk)

        for line in content.splitlines():
            m = _HEADING_RE.match(line)
            if m:
                flush()
                level, title = len(m.group(1)), m.group(2).strip()
                if level == 1 and not heading_stack:
                    doc_title = title
                del heading_stack[level - 1:]
                heading_stack.append(title)
            else:
                buf.append(line)
        flush()

    def _rebuild_df(self) -> None:
        self._df.clear()
        for chunk in self.chunks:
            for token in chunk.tokens:
                self._df[token] += 1

    # ---------------------------------------------------------------- search

    def search(self, query: str, limit: int = 5) -> list[tuple[float, Chunk]]:
        """Rank chunks by TF-IDF-weighted overlap with the query."""
        q_tokens = _tokenize(query)
        if not q_tokens or not self.chunks:
            return []

        n = len(self.chunks)
        scored: list[tuple[float, Chunk]] = []
        for chunk in self.chunks:
            score = 0.0
            for token in q_tokens:
                tf = chunk.tokens.get(token, 0)
                if tf == 0:
                    continue
                idf = math.log(1 + n / (1 + self._df[token]))
                score += (1 + math.log(tf)) * idf
            if score > 0:
                # Boost matches in the section heading — headings are dense signal.
                heading_tokens = set(_tokenize(chunk.section + " " + chunk.doc_title))
                if any(t in heading_tokens for t in q_tokens):
                    score *= 1.5
                scored.append((score, chunk))

        scored.sort(key=lambda pair: -pair[0])
        return scored[:limit]

    # ------------------------------------------------------------------ get

    def get(self, ref: str) -> Chunk | None:
        """Fetch a chunk by its `ref` (doc path, optionally #section)."""
        if "#" in ref:
            doc_path, section = ref.split("#", 1)
        else:
            doc_path, section = ref, None

        for idx in self._by_doc.get(doc_path, []):
            chunk = self.chunks[idx]
            if section is None or chunk.section == section:
                return chunk
        return None

    def list_documents(self) -> list[dict]:
        out = []
        for doc_path, idxs in sorted(self._by_doc.items()):
            first = self.chunks[idxs[0]]
            out.append({
                "path": doc_path,
                "title": first.doc_title,
                "sections": [self.chunks[i].section for i in idxs if self.chunks[i].section],
            })
        return out
