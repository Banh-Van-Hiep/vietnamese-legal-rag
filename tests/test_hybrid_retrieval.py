from team1_data.retrieval.hybrid import HybridRetriever
import time

from team1_data.retrieval.errors import RetrievalUnavailableError

class FakeRetriever:
    def __init__(self, results=None, error=None):
        self.results = results or []
        self.error = error

    def _search(self, question, limit):
        if self.error:
            raise self.error
        return self.results


def make_row(chunk_id):
    return {"chunk_id": chunk_id, "content": f"Content {chunk_id}"}


def test_hybrid_retriever_combines_bm25_and_dense():
    bm25 = FakeRetriever([make_row("A"), make_row("B")])
    dense = FakeRetriever([make_row("B"), make_row("C")])

    retriever = HybridRetriever(bm25, dense)
    result = retriever.retrieve("luật doanh nghiệp", top_k=3)

    assert result["question"] == "luật doanh nghiệp"
    assert [row["chunk_id"] for row in result["results"]] == ["B", "A", "C"]
    assert all(
        row["retrieval_method"] == "hybrid_rrf"
        for row in result["results"]
    )


def test_hybrid_retriever_raises_when_a_branch_fails():
    bm25 = FakeRetriever([make_row("A")])
    dense = FakeRetriever(error=RuntimeError("Qdrant unavailable"))

    retriever = HybridRetriever(bm25, dense)

    try:
        retriever.retrieve("luật doanh nghiệp")
    except Exception as exc:
        from team1_data.retrieval.errors import RetrievalUnavailableError
        assert isinstance(exc, RetrievalUnavailableError)
    else:
        raise AssertionError("Expected RetrievalUnavailableError")

class SlowRetriever:
    def _search(self, question, limit):
        time.sleep(2)
        return []


def test_hybrid_retriever_times_out():
    bm25 = SlowRetriever()
    dense = SlowRetriever()

    retriever = HybridRetriever(
        bm25,
        dense,
        timeout=0.2,
    )

    start = time.monotonic()

    try:
        retriever.retrieve("luật doanh nghiệp")
    except RetrievalUnavailableError:
        elapsed = time.monotonic() - start
        assert elapsed < 1.0, f"Timeout took too long: {elapsed:.2f}s"
    else:
        raise AssertionError("Expected RetrievalUnavailableError")

