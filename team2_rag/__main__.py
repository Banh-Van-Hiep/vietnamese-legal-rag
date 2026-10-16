"""Demo cục bộ: python -m team2_rag (mock) hoặc --rerank-file <json> (luồng Context -> LLM)."""

import argparse
import json

from .service import generate_answer, query, to_error_response


def _offline_llm(rerank_output):
    """FakeLLMProvider mô phỏng LLM: trích dẫn chunk đầu tiên với metadata sao chép đúng. CHỈ để demo/test offline."""
    from .llm.fake import FakeLLMProvider
    from .llm.service import LLMService
    first = rerank_output["results"][0]
    cite = {"citation_id": "C1", **{k: first[k] for k in ("chunk_id", "document_id", "article_id", "document_title", "article", "clause", "point", "source_url")}}
    reply = {"status": "answered", "answer": "[Mô phỏng offline, không phải LLM thật] Xem nguồn được trích dẫn [C1].", "citations": [cite]}
    return LLMService(FakeLLMProvider([reply]))


def main() -> None:
    parser = argparse.ArgumentParser(description="Team 2 RAG demo")
    parser.add_argument("--question", default="Câu hỏi dùng để kiểm thử")
    parser.add_argument("--scenario", choices=["answered", "insufficient_context"], default="answered")
    parser.add_argument("--rerank-file", help="JSON output của Reranker (question + results 12 trường Team 1)")
    parser.add_argument("--offline", action="store_true", help="với --rerank-file: dùng LLM giả lập, không cần API key")
    args = parser.parse_args()
    if not args.rerank_file:
        print(json.dumps(query(args.question, [], scenario=args.scenario), ensure_ascii=False, indent=2))
        return
    with open(args.rerank_file, encoding="utf-8") as f:
        data = json.load(f)
    try:
        result = generate_answer(data, llm_service=_offline_llm(data) if args.offline else None)
    except Exception as exc:  # demo CLI: in lỗi theo ErrorResponse nếu là lỗi LLM
        result = to_error_response(exc) or {"error": {"code": type(exc).__name__, "message": str(exc)}}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
