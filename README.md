# Vietnamese Legal RAG Assistant

Project xây dựng trợ lý hỏi đáp pháp luật Việt Nam dựa trên Retrieval-Augmented Generation (RAG). Repository này hiện chỉ cung cấp cấu trúc dự án, phân công trách nhiệm và các điểm thống nhất giữa các team; chưa chứa implementation.

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
User
```

Hybrid Retrieval và RRF nằm trong phạm vi Team 1. Team 2 bắt đầu với candidate chunks do Team 1 cung cấp và phụ trách phần RAG/LLM. Team 3 tích hợp trải nghiệm ứng dụng cho người dùng.

## Team Responsibilities

### Team 1 — Data & Retrieval (`team1_data/`)

Phụ trách legal data, data cleaning, chunking, metadata, BM25 retrieval, dense retrieval, embedding, vector store/vector database, hybrid retrieval, RRF và retrieval evaluation. Hybrid Retrieval và RRF thuộc Team 1, không thuộc Team 2.

### Team 2 — RAG & LLM (`team2_rag/`)

Phụ trách reranker, context builder, prompt, LLM, citation, RAG pipeline, RAG evaluation, answer quality, hallucination/grounding và citation verification.

### Team 3 — Fullstack (`team3_fullstack/`)

Phụ trách backend, REST API, frontend, UI/UX, document viewer, integration và deployment.

## Repository Structure

```text
.
├── .github/       # CODEOWNERS và Pull Request template
├── configs/       # Tài liệu về cấu hình dùng chung
├── contracts/     # Nguyên tắc interface/data contract giữa các team
├── docs/          # Tài liệu project
├── evaluation/    # Tài liệu evaluation dùng chung
├── scripts/       # Vị trí dành cho utility scripts trong tương lai
├── team1_data/    # Phạm vi Team 1: Data & Retrieval
├── team2_rag/     # Phạm vi Team 2: RAG & LLM
├── team3_fullstack/ # Phạm vi Team 3: Fullstack
└── tests/         # Vị trí dành cho integration/E2E tests dùng chung
```

Các thư mục team độc lập về implementation. Những file hiện có chỉ mô tả phạm vi và nguyên tắc làm việc, chưa triển khai source code.

## Shared Contracts

`contracts/` là nơi thống nhất dữ liệu trao đổi giữa các team, không áp đặt cách triển khai bên trong từng team. Luồng giao tiếp dự kiến:

```text
Team 1 -- Retrieval results / chunks --> Team 2
Team 2 -- Answer + citations ---------> Team 3
Team 3 -- User question --------------> Team 2
```

Các schema và chi tiết interface sẽ được thống nhất sau; hiện chưa có contract implementation.

## Development Workflow

- Đọc README của team và tài liệu trong `contracts/` trước khi tích hợp liên team.
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