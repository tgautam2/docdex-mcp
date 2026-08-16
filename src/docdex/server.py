"""MCP server exposing a documentation knowledge base to AI clients.

Run:  python -m docdex.server --docs ./sample_docs

Tools exposed:
  search_docs(query, limit)  -> ranked chunks with refs
  get_section(ref)           -> full text of one chunk
  list_docs()                -> corpus overview (titles + section outline)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from mcp.server import MCPServer

from .index import KnowledgeIndex

server = MCPServer(
    name="docdex",
    instructions=(
        "Knowledge-base server over a local documentation corpus. "
        "Use search_docs to find relevant sections, then get_section to read "
        "one in full. Always cite the ref of any section you rely on."
    ),
)

_index = KnowledgeIndex()


@server.tool()
def search_docs(query: str, limit: int = 5) -> list[dict]:
    """Search the documentation corpus. Returns ranked matching sections,
    each with a `ref` usable with get_section, a relevance score, and a
    short excerpt."""
    results = _index.search(query, limit=max(1, min(limit, 20)))
    return [
        {
            "ref": chunk.ref,
            "doc": chunk.doc_title,
            "section": chunk.section or "(top of document)",
            "score": round(score, 3),
            "excerpt": chunk.text[:400],
        }
        for score, chunk in results
    ]


@server.tool()
def get_section(ref: str) -> dict:
    """Fetch the full text of one documentation section by its ref
    (as returned by search_docs)."""
    chunk = _index.get(ref)
    if chunk is None:
        return {"error": f"no section found for ref: {ref}"}
    return {
        "ref": chunk.ref,
        "doc": chunk.doc_title,
        "section": chunk.section or "(top of document)",
        "text": chunk.text,
    }


@server.tool()
def list_docs() -> list[dict]:
    """List every document in the corpus with its section outline."""
    return _index.list_documents()


def main() -> None:
    parser = argparse.ArgumentParser(description="Knowledge-base MCP server")
    parser.add_argument("--docs", required=True, help="Path to a directory of .md files")
    args = parser.parse_args()

    n = _index.load_directory(args.docs)
    print(f"docdex-mcp: indexed {n} sections from {args.docs}", file=sys.stderr)
    server.run()  # stdio transport by default


if __name__ == "__main__":
    main()
