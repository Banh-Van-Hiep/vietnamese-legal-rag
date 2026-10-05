# Team 2 — RAG & LLM: Week 1

Phạm vi: thiết kế hỏi đáp pháp luật lao động, ưu tiên Bộ luật Lao động 2019.
Đây là thiết kế để review, chưa phải runtime hoặc kết quả benchmark.
Nguồn chuẩn: [Contract v0.1 Revision 2](../../contracts/v0.1/README.md).
Không thay đổi bốn schema chung, dữ liệu/code Team 1, frontend/backend Team 3 hoặc deployment.

## Deliverables

| Task | Tài liệu | Nội dung review |
| --- | --- | --- |
| VLRA-9 | [Flow](rag-flow.md), [I/O](rag-io-specification.md), [ví dụ](examples/) | Sơ đồ E2E, phân biệt public/internal, đúng v0.1 |
| VLRA-10 | [Reranker](reranker-design.md), [Context](context-builder.md), [Prompt](prompt-design.md) | Model đề xuất, thuật toán/token budget, system prompt |
| VLRA-11 | [LLM](llm-proposal.md), [Citation](citation-specification.md) | Bốn model, chi phí có nguồn, marker/provenance |

[Review liên team](cross-team-review.md) ghi snapshot GitHub và các điểm mở của PR #7.
[Schema cũ](schemas/README.md) chỉ còn alias hoặc bản nháp deprecated, không phải contract thứ hai.

## Kiểm tra tài liệu

Từ gốc repository:

```bash
python -m pip install jsonschema==4.25.1
python docs/team2_rag/validate_week1.py
git diff --check
git diff --name-only
```

Validator cần jsonschema và referencing trong môi trường phát triển.
Nó chỉ kiểm tra fixture/schema và marker/provenance, không chạy RAG/model/API.
Không cài model/SDK hoặc thay dependency runtime trong Week 1.

## Bàn giao

PR cá nhân → feature/team2-rag; sau review liên team mới PR → develop.
Không tự tick Jira Done hoặc tự merge. Hoàn tất thiết kế không đồng nghĩa
pipeline đã chạy hoặc các vấn đề tích hợp đã được phê duyệt.
