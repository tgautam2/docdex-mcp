# DocDex — Documentation MCP Server

An MCP (Model Context Protocol) server that turns a directory of markdown
documentation — wikis, runbooks, policy docs — into tools an AI assistant can
search and cite. Point it at a docs folder; Claude (or any MCP client) can
then find, read, and reference specific sections instead of guessing.

## Tools exposed

| Tool | What it does |
|---|---|
| `search_docs(query, limit)` | Ranked search over all sections; returns refs + excerpts |
| `get_section(ref)` | Full text of one section by its stable ref |
| `list_docs()` | Corpus overview: every doc with its section outline |

The server's instructions tell the model to **cite the ref of any section it
relies on** — retrieval you can audit, not vibes.

## Design decisions

- **Heading-based chunking.** Docs are split at markdown headings, and each
  chunk carries its full heading path (`Runbook > Rollback procedure`). Refs
  are stable (`path#heading-path`), so a citation today still resolves
  tomorrow if the doc hasn't changed.
- **TF-IDF keyword ranking, no embeddings.** Deliberate: zero external
  services, zero API keys, runs anywhere, and results are *inspectable* —
  you can see exactly why a chunk ranked. Heading matches get a 1.5x boost
  because headings are dense signal. The `KnowledgeIndex` class is isolated
  from MCP wiring specifically so the ranker can be swapped for embeddings
  without touching the server.
- **Search-then-fetch, not dump-everything.** `search_docs` returns short
  excerpts; the model calls `get_section` only for what it needs. Keeps
  context windows small on large corpora.

## Quick start

```bash
pip install mcp
PYTHONPATH=src python -m docdex.server --docs ./sample_docs
```

### Claude Desktop config

```json
{
  "mcpServers": {
    "docdex": {
      "command": "python",
      "args": ["-m", "docdex.server", "--docs", "/path/to/your/docs"],
      "env": { "PYTHONPATH": "/path/to/docdex-mcp/src" }
    }
  }
}
```

Then ask Claude things like *"what's our rollback procedure?"* or *"how long
do we keep debug logs?"* — it will search, fetch the section, and cite the ref.

## Tests

```bash
python tests/test_index.py
```

Covers: relevant-section ranking, heading-boost ordering, ref roundtrips,
unknown-ref handling, corpus listing, and empty/stopword-only queries.

## Layout

```
src/docdex/index.py    KnowledgeIndex — chunking, TF-IDF search, refs (MCP-free)
src/docdex/server.py   MCP wiring — 3 tools over the index
sample_docs/           small policy + runbook corpus to try it on
tests/test_index.py    index test suite (no pytest dependency)
```

## Extension ideas

- Pluggable embedding ranker (the index/server split exists for this)
- File-watcher for live reindexing on doc edits
- Confluence / Notion loaders alongside the markdown loader
- Per-source access scoping for multi-team corpora
