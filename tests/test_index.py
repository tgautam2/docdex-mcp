"""Tests for the knowledge index. Run: python -m pytest tests/ -q
(or plain `python tests/test_index.py` — no pytest required)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from docdex.index import KnowledgeIndex  # noqa: E402

DOCS = Path(__file__).resolve().parent.parent / "sample_docs"

failures = 0


def check(cond, msg):
    global failures
    if not cond:
        print(f"FAILED: {msg}")
        failures += 1


def make_index():
    idx = KnowledgeIndex()
    n = idx.load_directory(DOCS)
    check(n >= 10, f"expected >=10 chunks, got {n}")
    return idx


def test_search_finds_relevant_section():
    idx = make_index()
    results = idx.search("how long are debug logs retained")
    check(len(results) > 0, "retention query returned nothing")
    top = results[0][1]
    check("Retention" in top.section or "Retention" in top.doc_title,
          f"expected retention section on top, got {top.ref}")


def test_search_ranks_heading_matches_higher():
    idx = make_index()
    results = idx.search("rollback procedure")
    check(len(results) > 0, "rollback query returned nothing")
    check(results[0][1].section == "Deployment and Rollback Runbook > Rollback procedure",
          f"expected rollback section first, got {results[0][1].ref}")


def test_get_by_ref_roundtrip():
    idx = make_index()
    results = idx.search("severity levels")
    ref = results[0][1].ref
    fetched = idx.get(ref)
    check(fetched is not None, f"get() failed for ref {ref}")
    check(fetched.ref == ref, "roundtrip ref mismatch")
    check("SEV1" in fetched.text, "expected SEV1 in severity section text")


def test_get_unknown_ref_returns_none():
    idx = make_index()
    check(idx.get("nope.md#Nothing") is None, "unknown ref should return None")


def test_list_documents():
    idx = make_index()
    docs = idx.list_documents()
    check(len(docs) == 4, f"expected 4 docs, got {len(docs)}")
    paths = {d["path"] for d in docs}
    check("policies/data-retention.md" in paths, "missing data-retention doc")
    check(all(d["sections"] for d in docs), "every doc should have sections")


def test_empty_query():
    idx = make_index()
    check(idx.search("") == [], "empty query should return []")
    check(idx.search("the and of") == [], "stopword-only query should return []")


if __name__ == "__main__":
    test_search_finds_relevant_section()
    test_search_ranks_heading_matches_higher()
    test_get_by_ref_roundtrip()
    test_get_unknown_ref_returns_none()
    test_list_documents()
    test_empty_query()
    if failures:
        print(f"{failures} test(s) failed.")
        sys.exit(1)
    print("All tests passed.")
