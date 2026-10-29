# Biên bản nghiệm thu Team 3 — Tuần 5

**Ngày kiểm chứng:** 30/10/2026. **Nhiệm vụ:** [tasks.md](tasks.md).

## 1. Kết luận

**Chưa đủ điều kiện nghiệm thu toàn bộ tuần 5.**

VLRA22, VLRA23 và T3-06 đạt phạm vi mock. VLRA24 còn xung đột ID `gold_041`,
cơ cấu Golden chưa đạt DoD và chờ Team2 kiểm chứng nội dung/căn cứ.

## 2. Expected / Actual theo task

| Task | Expected / DoD | Actual ngày30/10 | Kết luận |
| --- | --- | --- | --- |
| **VLRA22** | Public SSE đúng frame/no-store/55s, REST hội thoại, curl -N, disconnect an toàn | Maven125/125 gồm12 StreamApiTests; curl -N trả200, UTF-8 đúng, meta→delta→complete và header đúng. REST list/messages/delete đạt. HTTP test kiểm heartbeat, disconnect và replay không gọi AI lại; source có callback completion/error/timeout. | **Đạt kiểm chứng mock**; Java cần PostgreSQL và Python mock, không cần AI/index thật. |
| **VLRA23** | Chat/sidebar/parser; gửi tới mock backend, nối delta, bấm C1 mở Viewer đúng mẫu | FE72/72 và tsc/Vite build đạt; E2E10/10 qua Java thật và FastAPI mock. E02 hỏi đầu, E03 mở C1/đúng nguyên văn, E04 tiếp nối, E05 reload history, E07 thiếu căn cứ, E08–E09 lỗi/thử lại. Không uncaught JS exception. | **Đạt kỹ thuật mock**. Không coi một delta chứa answer là streaming token từ model. |
| **VLRA24** | Bộ chung30–50 câu, validation/dedup; P0 thành lập10, vốn/cổ đông8, quản trị8, giải thể4, thiếu dữ kiện10 | File chung Team2 có50 câu:49 answered/1 insufficient; validator50/50, không trùng ID/câu hỏi sau chuẩn hóa. Đã thay4 câu trùng ý và thu hẹp2 câu tổng hợp; không còn bản riêng Team3. Chưa xác nhận cơ cấu10/8/8/4/10; gold_041 xung đột nội dung với fixture5 câu, gây1 test lỗi. | **Team3 hoàn tất phần đóng góp/hợp nhất, chuyển Team2 kiểm chứng**. Chưa nghiệm thu dataset: xung đột ID gold_041, cơ cấu49/1 khác DoD và chờ Team2 duyệt nội dung. |
| **VLRA-T3-06** | CORS/trace header, cấu hình môi trường, integration mock100% | 37/37 harness cấu hình; HTTP test/CORS và curl/REST7/7 đạt. Allowed origin localhost:5173 preflight200, origin ngoài danh sách403 không ACAO; request FE thực15173 tới BE18043 thành công. Meta/complete/UUID được kiểm contract76/76 +4 wire payload. | **Đạt local**; runner dùng Maven stub, không phải37 lần Spring startup thật. |

## 3. Dataset Phase1: kết quả hợp nhất và phần chưa đạt

| Tập dữ liệu hiện hành | Tổng | answered | insufficient_context | ID/câu hỏi trùng sau chuẩn hóa |
| --- | ---: | ---: | ---: | ---: |
| team2_rag/data/golden/golden_phase1_30cai.json | 50 | 49 | 1 | 0/0 |

- Validator đạt50/50; không trùng ID/câu hỏi sau chuẩn hóa; các câu trùng ý đã được xử lý.
- Hiện49 answered/1 insufficient_context. Theo DoD10 mẫu insufficient, còn thiếu9; cơ cấu P0 chưa được xác nhận.
- `gold_041` trong Phase1 hỏi về chuyển nhượng cổ phần ưu đãi biểu quyết, còn fixture5 câu dùng cùng ID cho câu hỏi thuế thu nhập cá nhân.
- Test `test_sample_ids_do_not_collide_with_full_golden` tại `team2_rag/tests/test_answer_citation_accuracy.py:70` FAIL. Bộ mở rộng:388 đạt,1 lỗi,147 subtest đạt.
- Team3 phối hợp Team2 thống nhất ID để mỗi ID chỉ một câu hỏi, sau đó chạy lại hồi quy; Team2 kiểm chứng nội dung/cơ cấu bộ chung.

## 4. Kiểm chứng và bằng chứng

### 4.1. Tổng hợp

| Kiểm tra | Kết quả |
| --- | --- |
| Maven Wrapper package | 125/125, 0 fail/error/skip; gồm16 H2 +16 PostgreSQL,12 HTTP/SSE |
| Frontend unit | 72/72, 0 fail |
| Frontend build | tsc -b + Vite production build PASS |
| Config runner | 37/37; khôi phục env/location |
| Browser E2E | 10/10; 0 uncaught JS exception; chính FastAPI mock Team2 |
| curl/CORS/REST | 7/7: stream UTF-8, allowed/denied origin, list, messages, delete, deleted history |
| Public schema/semantic | 76/76 (15 positive,61 negative),4 payload thật và binding PASS |
| Golden validator/kiểm bổ sung | 50/50 exit0; UTF-8/NFC/ID/câu hỏi/chunk đạt trong Phase1; xung đột gold_041 với fixture5 câu |
| Hồi quy nội bộ mở rộng | 388 đạt,1 lỗi gold_041,147 subtest đạt |

### 4.2. Môi trường

JDK25, Node24.21, Python3.12, PostgreSQL18 và Edge headless.
Luồng kiểm tra: React → Java → PostgreSQL → FastAPI HTTP mock.

### 4.3. Bằng chứng kiểm chứng

Kết quả tại `backend/target/final-acceptance-20261030/`: summary.json,
e2e/results.json, http-smoke.json, golden-validator.log và internal-regression-rerun.log.

## 5. Kết luận nghiệm thu và bước tiếp theo

- VLRA22, VLRA23 và T3-06: đủ điều kiện chốt kỹ thuật với mock.
- VLRA24: chưa chốt; Team3/Team2 thống nhất ID gold_041, Team2 kiểm chứng nội dung/căn cứ và cơ cấu bộ chung.

## 6. Nội dung bàn giao

1. **Team3/Team2:** thống nhất ID `gold_041` giữa `golden_phase1_30cai.json` và `golden_sample_5qa.json`; chạy lại test không xung đột ID.
2. **Team2:** xác nhận nội dung/căn cứ và nhóm P0. Bộ50 câu hiện49 answered/1 insufficient; chỉ tiêu10 insufficient còn thiếu9, cần bố trí lại trong trần50.
3. **Team3:** tiếp nhận kết quả để khép VLRA24.

[Kiểm chứng Golden](vlra24-team3-golden/validation.md).
