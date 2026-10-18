# Team 2 — RAG & LLM

## Scope Week 1

Thiết kế cho demo pháp luật lao động, ưu tiên Bộ luật Lao động 2019. Team 2 nhận candidate từ Team 1, làm rerank/context/prompt/LLM/citation và trả kết quả cho Backend Team 3. Week 1 bàn giao tài liệu thiết kế; chưa triển khai RAG hoặc benchmark model.

| Task | Tài liệu |
| --- | --- |
| VLRA-9 — Luồng RAG và I/O | [rag-flow.md](rag-flow.md), [rag-io-specification.md](rag-io-specification.md) |
| VLRA-10 — Reranker, context, prompt | [reranker-design.md](reranker-design.md), [context-builder.md](context-builder.md), [prompt-design.md](prompt-design.md) |
| VLRA-11 — LLM và citation | [llm-proposal.md](llm-proposal.md), [citation-specification.md](citation-specification.md) |

## Nguồn đối chiếu và ranh giới

Bản thiết kế này dựa trên `develop` tại `a80f44b`: [đặc tả Team 3 v1.2](https://github.com/Banh-Van-Hiep/vietnamese-legal-rag/blob/a80f44b248b80ea39155b8029ddc132686a1e907/docs/team3_fullstack/team3.md), mục 1.6–1.10, và [retrieval design của Team 1](https://github.com/Banh-Van-Hiep/vietnamese-legal-rag/blob/a80f44b248b80ea39155b8029ddc132686a1e907/docs/team1_data/retrieval-design.md). Các endpoint trong đặc tả vẫn là thiết kế, không chứng minh đã có runtime.

Team 1 sở hữu corpus, chunking, metadata, retrieval, hybrid/RRF và nguồn nguyên văn điều luật. Team 3 sở hữu API công khai, hội thoại, lưu dữ liệu, frontend và document viewer. Tham số rerank/context/LLM trong tài liệu Team 2 là lựa chọn khởi đầu để review.

Các file trong [schemas/](schemas/) được giữ nguyên từ bản nháp Team 2 trước đây. Chúng còn dùng tên `document/source`, response thiếu `status` và chưa mô tả `history`; **không dùng chúng để xác nhận tương thích v1.2**. Cấu trúc tích hợp trong Markdown bám theo docs Team 1/3; việc cập nhật schema chung cần được các team thống nhất riêng trước implementation.
