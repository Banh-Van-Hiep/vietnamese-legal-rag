# Vietnamese Legal RAG Assistant

Project xây dựng trợ lý hỏi đáp pháp luật doanh nghiệp Việt Nam dựa trên Retrieval-Augmented Generation (RAG). Người mới (và AI agent) đọc [AGENTS.md](AGENTS.md) trước: file này chỉ đường tới code, tài liệu, lệnh setup và lệnh kiểm chứng của từng team. Đặc tả chuẩn là [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Kết quả mock được phân biệt với pipeline RAG thật.

## System Flow

```text
User Question
	↓
Team 1 — Retrieval
	↓
Candidate Chunks
	↓
Team 2 — Reranker
	↓
Context Builder
	↓
Prompt
	↓
LLM
	↓
Answer + Citation
	↓
Team 3 — Backend / Frontend
	↓
User.
```

Hybrid Retrieval và RRF nằm trong phạm vi Team 1. Team 2 bắt đầu với candidate chunks do Team 1 cung cấp và phụ trách phần RAG/LLM. Team 3 tích hợp trải nghiệm ứng dụng cho người dùng.

## Team Responsibilities

### Team 1 — Data & Retrieval (`data/`, `team1_data/`, `evaluation/`)

Phụ trách legal data, data cleaning, chunking, metadata, Article Store, BM25 retrieval, dense retrieval, embedding, vector store, hybrid retrieval (RRF), Golden Dev Set và retrieval evaluation. Chỉ dẫn: [team1_data/AGENTS.md](team1_data/AGENTS.md).

### Team 2 — RAG & LLM (`team2_rag/`)

Phụ trách reranker, context builder, prompt, LLM client, citation verification, FastAPI AI service (`/internal/v1/*`), RAG evaluation và benchmark. Chỉ dẫn: [team2_rag/AGENTS.md](team2_rag/AGENTS.md).

### Team 3 — Fullstack (`team3_fullstack/`)

Phụ trách backend Spring Boot, public API/SSE, frontend React, Document Viewer, đo latency end-to-end và deployment. Chỉ dẫn: [team3_fullstack/AGENTS.md](team3_fullstack/AGENTS.md).

## Repository Structure

```text
.
├── AGENTS.md              # Điểm vào cho người mới và AI agent: bản đồ repo, bất biến, lệnh kiểm chứng
├── .github/               # CODEOWNERS, Pull Request template, workflow CI
├── configs/               # File env mẫu (team2-api.env.example)
├── contracts/v0.1/        # Contract JSON Schema giữa các team (xem CONTRACT.md)
├── data/
│   ├── doanh-nghiep/      # Corpus P0: raw, interim, processed (chunks.jsonl, articles.jsonl), registry
│   └── doanh-nghiep-mo-rong/  # Corpus mở rộng 1.000 văn bản, chưa dùng trong runtime
├── docs/
│   ├── ARCHITECTURE.md    # Đặc tả chuẩn
│   ├── REQUIREMENTS.md    # BR, NFR-10..16, truy vết, cổng nghiệm thu
│   ├── CODING_CONVENTIONS.md
│   ├── decisions/         # ADR: vì sao nhóm chọn như vậy
│   └── team1_data/ team2_rag/ team3_fullstack/   # Thiết kế và báo cáo của từng team
├── evaluation/retrieval/  # Cấu hình và kết quả các lượt đánh giá retrieval
├── notebooks/             # Notebook chạy benchmark trên Colab
├── scripts/               # Script dùng chung, gồm harness_verify.py (4 cổng kiểm chứng)
├── team1_data/            # Code retrieval, Golden Dev Set, evaluation; docs_1/ là task theo tuần
├── team2_rag/             # Code RAG/LLM và AI service; docs_2/ là task theo tuần
├── team3_fullstack/       # backend/ (Spring Boot), frontend/ (React), tools/; docs_3/ là task theo tuần
└── tests/                 # Test Python dùng chung, kiểm chỗ các team gặp nhau
```

Thiết kế ổn định nằm trong `docs/teamX_*/`; kế hoạch và kết quả từng tuần nằm trong `teamX_*/docs_X/weekN/tasks.md`. Không suy ra trạng thái RAG thật từ mock hoặc từ một báo cáo cũ.

## Shared Contracts

`contracts/v0.1/` là nơi thống nhất dữ liệu trao đổi giữa các team, không áp đặt cách triển khai bên trong từng team. Đọc [contracts/v0.1/CONTRACT.md](contracts/v0.1/CONTRACT.md) để biết schema nào dùng ở ranh giới nào.

```text
Frontend --query_request / chat_stream--> Java backend
Java backend --POST /internal/v1/query--> Team 2 AI service --rag_response--> Java backend
Team 1 --retrieval_output / internal_article--> Team 2
```

Schema trong `docs/team2_rag/schemas/` là bản nháp cũ của Team 2, không dùng để validate giao tiếp giữa các team.

## Development Workflow

- Đọc `AGENTS.md` (gốc và của team) và tài liệu trong `contracts/` trước khi sửa code hoặc tích hợp liên team.
- Chạy `python scripts/harness_verify.py` trước khi mở Pull Request; CI chạy lại các cổng này cho mỗi PR vào `develop`.
- Giữ implementation nội bộ trong phạm vi team phụ trách.
- Cập nhật tài liệu khi thay đổi phạm vi hoặc interface dùng chung.
- Không commit API key, password hoặc secret; dùng `.env.example` làm danh sách placeholder.
- Tạo/cập nhật test phù hợp với thay đổi khi implementation được bổ sung.

## Branching Workflow

```text
main
  ↑
develop
  ↑
feature/*
```

- Không push trực tiếp vào `main` hoặc `develop`.
- Mỗi thành viên làm việc trên nhánh `feature/*`.
- Tạo Pull Request từ `feature/*` vào `develop`.
- Pull Request cần được review trước khi merge.
- Merge `develop` vào `main` khi phát hành release.
