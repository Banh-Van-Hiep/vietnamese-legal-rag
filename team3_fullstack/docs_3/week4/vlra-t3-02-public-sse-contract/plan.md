# Implementation Plan: Public SSE contract

**Date:** 2026-10-29. **Spec:** [spec.md](spec.md). Không đổi nhánh làm việc.

## Summary

Sửa query_request.schema.json tại contracts/v0.1/ cho ChatRequest theo baseline hiện hành;
thêm chat_stream.schema.json với Meta/Delta/Complete/ErrorResponse/PublicCitation.
CONTRACT.md định nghĩa mapping/framing/semantics, public_examples.json chứa mock;
validate_public_contract.py kiểm schema,
fixture và dữ liệu thực do StreamApiTests xuất ra. Các payload không phải raw SSE stream.

## Technical Context

JSON Schema Draft 2020-12; Python >=3.10/jsonschema đã có trong môi trường kiểm thử.
Không dependency/runtime/storage mới; không đổi Java25/Boot4.1.1/React hiện có.
Chạy offline, không gọi provider hoặc tải model. Không đặt ngưỡng coverage/hiệu năng mới.
Schema cấu trúc dùng additionalProperties=false, UUIDv4, ID integer1..9007199254740991,
UTC và các giới hạn Unicode/status/citation đã chốt. Kiểm semantic riêng để không hứa
schema tự kiểm marker, ID binding, legal provenance hoặc thứ tự sự kiện.
Schema ChatRequest kiểm biểu diễn đã chuẩn hóa question sau strip; không mô tả bước
HTTP decoder/trim bằng một maxLength áp nhầm lên raw body còn khoảng trắng ngoài.
README và validator nêu ranh giới này; không tự chuẩn hóa/sửa payload sai trong validator.

## Constitution Check

Trước/sau thiết kế: PASS bốn nguyên tắc API compatibility, ranh giới team, tái sử dụng,
kiểm chứng. Người dùng cho phép sửa trực tiếp public request gốc, thay quyết định giữ file cũ.
Schema này không còn kiểm JSON legacy; ghi cảnh báo chuyển đổi rõ ràng. Team 1/2 không thay đổi.
Không lấy link constitution lịch sử bị thiếu làm yêu cầu mới; ARCHITECTURE là baseline.
Đưa qua review khi bàn giao, không tự commit/push hoặc xác nhận đã có review liên team.

## Project Structure

- contracts/v0.1/query_request.schema.json: đúng tên cũ, root ChatRequest, cập nhật camelCase/ID số.
- contracts/v0.1/chat_stream.schema.json: payload SSE, tham chiếu ID/UUID từ request schema.
- contracts/v0.1/public_examples.json: fixture mock.
- contracts/v0.1/validate_public_contract.py: validator offline, Registry chỉ dùng schema local.
- contracts/v0.1/CONTRACT.md và contracts/README.md: mapping từng file/boundary,
  cảnh báo schema request không còn kiểm JSON legacy; thư mục v0.1 giữ để không đổi path.
- Bỏ bộ public trùng vừa tạo sau khi kiểm đủ nội dung, đúng file/checksum; chỉ xóa thư mục rỗng.
- Hồ sơ tuần này: spec/plan/tasks/research/data-model/quickstart/contracts-reference/validation.
- docs/team3_fullstack/: dẫn schema và ghi đúng xác nhận vai trò, không tên cá nhân.
- docs_3/week4/verification.md: khép W4-02/03/05 theo bằng chứng và xác nhận;
  W4-04 tách quy trình đã xác nhận khỏi enforcement GitHub chưa đọc được.

## Phases và kiểm chứng

0. [research.md](research.md): quyết định từ nguồn/repo, không còn unknown chặn schema.
1. [data-model.md](data-model.md), [contract reference](contracts/README.md),
   [quickstart.md](quickstart.md): xác định dữ liệu và lệnh, chưa triển khai.
2. tasks -> analyze chỉ đọc; sửa vấn đề thiết kế được phép rồi kiểm lại trước implement.
3. Snapshot hash schema nội bộ/.github/source/dataset; tạo schema/fixtures/validator; chạy ca sai.
4. Chạy StreamApiTests/MockApiTests hiện có và regression API Team2; xuất wire mới, kiểm bằng validator mới. Đây là HTTP
   với upstream fixture, không phải LLM/live; không cần chạy lại full DB/FE khi code không đổi.
5. So hash, link/anchor, privacy và diff; cập nhật validation/biên bản và task checkbox.

## Boundaries

Legal ID lowercase theo CODING_CONVENTIONS. Runtime còn rộng hơn/NFC chưa tường minh:
ghi backlog, không nới schema theo code hoặc sửa code. Chỉ status/citation cardinality
là điều kiện schema; marker/order/unique chunk, URLs, UTC format và binding có kiểm riêng.
Không thêm endpoint REST, event SSE mới, public scenario/model/history hoặc auth.
