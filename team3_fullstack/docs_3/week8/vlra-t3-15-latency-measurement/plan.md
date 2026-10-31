# Implementation Plan: VLRA-T3-15 latency measurement

**Branch**: Team3 feature (baseline c62b4b4) | **Date**: 2026-10-31 | **Spec**: [spec.md](spec.md)
**Input**: T3-15 từ [nhiệm vụ tuần8](../tasks.md); bộ riêng tại thư mục này.

## Summary

Thêm runner Locust hữu hạn và timing opt-in tại StreamService. Giữ nguyên mọi public
payload/ID/trạng thái/persistence, chạy với PostgreSQL và FastAPI HTTP mock hiện có.
Live là bước riêng còn chờ Dev Set/runtime; chỉ đánh dấu phần đã kiểm chứng.

## Technical Context

- Java25/Spring Boot4.1.1; SLF4J/JsonMapper hiện có; không thêm Maven dependency.
- Python3.12; Locust2.43.1 riêng trong team3_fullstack/requirements-performance.txt, jsonschema/referencing hiện dùng trong repo.
- Windows local, tối đa5 người dùng cho công cụ; không đổi pool server theo ví dụ hoặc làm T3-16.
- Schema contracts/v0.1 hiện hành; gọi check_payload của validator public để tái sử dụng semantics.
- Report JSON/timing log; không thêm DB table hay API endpoint. Timing không lưu vào history.
- Kiểm thử: unittest, Maven Wrapper/JUnit, contract validator, runner với stack thật Java/PG/FastAPI HTTP mock.
- Mục tiêu: p95 client chat≤45s; article API≤1s; chưa là p95 render UI.

## Constitution Check

| Nguyên tắc | Trước thiết kế | Sau thiết kế |
| --- | --- | --- |
| API tương thích | PASS — đối chiếu SSE/citation/error | PASS — chỉ đo/log, schema không đổi |
| Ranh giới team | PASS | PASS — không sửa Team1/2, HTTP Python chỉ trong AiClient |
| Kiến trúc hiện tại | PASS | PASS — dùng project hiện có; Locust được task cho phép |
| Kiểm chứng | PASS — có kế hoạch test thành công/lỗi | PASS — smoke và live tách biệt; không claim model/Viewer UI |

Constitution có đường dẫn snapshot cũ; bốn nguyên tắc giữ nguyên, dùng ARCHITECTURE và
CODING_CONVENTIONS hiện hành làm căn cứ nghiệp vụ. Không sửa constitution ở task này.

## Project Structure

```text
team3_fullstack/
├── requirements-performance.txt
├── tools/measure_latency.py           # entrypoint Locust/gevent
├── tools/latency_report.py            # dataset/SSE/schema/timing/report helpers
├── tests/test_latency_report.py
├── tests/test_measure_latency.py
├── backend/src/main/java/com/legalai/backend/chat/stream/TurnTimings.java
├── backend/src/main/java/com/legalai/backend/chat/stream/StreamService.java
├── backend/src/main/resources/application-rag.properties
├── backend/src/test/java/com/legalai/backend/chat/stream/TurnTimingsTests.java
├── backend/src/test/java/com/legalai/backend/StreamApiTests.java
└── docs_3/week8/vlra-t3-15-latency-measurement/
    ├── spec.md, plan.md, research.md, data-model.md, quickstart.md
    ├── contracts/README.md
    ├── tasks.md, analysis.md, validation.md
    └── checklists/requirements.md
```

## Phases

1. Dataset/SSE/report core: strict JSON/Unicode/ID, reuse public schema, stream parser, nearest-rank, raw rows/counts/errors, exclusive output.
2. Java timings: monotonic measure in finally, bốn pha cộng dồn không chồng, replay/null/outcome/transport; upstream origin không chứa credentials/query; flag CHAT_LATENCY_ENABLED mặc định false. Observability lỗi không đổi kết quả request.
3. Locust finite runner: warm-up riêng, queue shared, clientRequestId UUIDv4 mới và trace lấy từ response header mỗi attempt, body complete trước stop, gevent total deadline; lookup citation đúng ID; event terminal riêng và report độc lập Locust header stats.
4. Provenance/join: live kiểm split_only format1, input150/dev90/test60, Dev hash/status/count khớp; readiness của RAG và origin trong telemetry. Thiếu timing/phase/replay không được PASS live. Không giả review hoặc model metrics.
5. Kiểm chứng và báo cáo: parser/schema/failure/provenance/unit timing, Maven regression, full stack smoke≥20 chat/20 lookup; public schema76ca và wire. Lưu evidence ignored, cập nhật validation/verification giữ form hiện có, không đổi tasks.md tổng tuần.

## Shared design

Cập nhật docs/team3_fullstack/performance-measurement.md và README.md với chức năng timing/runner; không đưa task tuần hoặc số liệu nghiệm thu vào tài liệu chung.

## Complexity Tracking

Không có vi phạm cần ngoại lệ. Không thêm công cụ triển khai, scheduler recovery,
API public, telemetry endpoint hay dịch vụ model mới.
