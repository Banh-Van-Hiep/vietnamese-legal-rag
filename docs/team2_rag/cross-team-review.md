# Review liên team — snapshot 05/10/2026

Kiểm tra 8 branch hiện có và 7 PR ở repository; đọc contract v0.1,
tài liệu retrieval/chunk/metadata Team 1 và API v1.2/DTO/UI mock Team 3.
Đây là review interface và phạm vi diff, không phải chứng nhận mọi code đã build/test.

## Branch so với develop

| Branch | SHA ngắn | Tình trạng |
| --- | --- | --- |
| develop | 0ce72d7 | Baseline tích hợp |
| feature/team1-data | 83b2286 | Ahead 5; PR #7 đang mở vào develop |
| feature/team2-rag | 8962022 | Ahead 2, behind 7; PR #6 đã merge contract vào Team 2 |
| feature/team2/datdo-contract | ec08ade | Branch PR #6 đã merge, còn tồn tại |
| feature/team3-fullstack | b6799c6 | Ahead 2, behind 6; đã nhận UI từ PR #4 |
| feature/team3/haunx | b7a1949 | Ahead 1, behind 7; PR #4 đã merge vào Team 3 |
| feature/team3/tuan | 2b0e377 | Behind 6; nội dung đã nằm trong develop |
| main | cf2abd7 | Behind 12; branch protected |

develop chưa có contracts/v0.1 của PR #6. UI static mới chưa vào develop.
Branch ahead/behind không chứng minh team đã/ chưa hoàn tất công việc trên Jira.
PR #3 đã đưa bản nháp tài liệu Team 2 vào develop; PR này chỉ hoàn thiện các tài liệu đó.
Không tự merge develop vào nhánh team khác hoặc kéo toàn bộ source của họ vào PR Team 2.

## Phạm vi sửa

Chỉ docs/team2_rag: tám tài liệu, review này, alias/deprecation schema cũ,
mock fixtures và validator tài liệu. Không thay đổi:
contracts/v0.1, docs/team1_data, docs/team3_fullstack, team3_fullstack,
docker-compose.yml, configs, pyproject.toml, root README hoặc CODEOWNERS.

Schema cũ được chuyển thành alias ở đường dẫn cũ, không xóa để tránh làm hỏng link.
Bốn schema chung giữ nguyên byte/field. Không thêm dependency runtime hoặc RAG service.

## PR #7: phản hồi thiết kế Team 2 (chưa đăng comment)

| Team 1 hỏi | Cách xử lý đề xuất không gây breaking change |
| --- | --- |
| Thêm document_number/issued_date/legal_status | Để v0.2 cần cả ba team review; v0.1 không gửi field dư |
| ID bl-45-2019-qh14-v1 / dieu-113 khác ví dụ Team 2 | Chấp nhận ID Team 1, schema đã cho phép; không đổi ID dữ liệu |
| Retrieval schema cũ 7 field | Alias tới schema chung 12 field; docs mới chỉ dùng v0.1 |
| Qdrant Docker/image | Thuộc Team 1/3; Team 2 không sửa deployment |

Đây là đề xuất trong docs, chưa phải phê duyệt thay mặt Team 1/3.
Document title dùng nguyên từ source; không suy số hiệu/ngày ban hành từ ID.
Team 1 có vài ví dụ metadata placeholder chưa đồng bộ; không dùng chúng làm ground truth.

## Điểm tích hợp cần thống nhất, không tự sửa code team khác

1. Context header: Team 1 để câu dẫn Điều trong context_header nhưng không đưa field này
   vào v0.1. Chunk R3 có câu dẫn Khoản trong content; trường hợp phụ thuộc câu dẫn Điều
   vẫn cần review. Team 2 không dùng content thiếu nghĩa để kết luận.
   Cần thống nhất một cách giữ ngữ cảnh hợp lệ hoặc contract mới trước runtime.
2. Team 3 v1.2 dùng snake_case, UUID, POST /api/v1/query đồng bộ, marker [C1].
   UI mock/code còn camelCase, conversationId dạng number, snippet, [1] và
   POST /api/v1/chat/stream. Backend DTO hiện phần lớn chỉ là skeleton.
   Đây là khoảng cách triển khai/đặc tả, không phải lý do đổi contract Team 2 theo mock.
3. History và document-viewer đã có trong đặc tả Team 3 nhưng ngoài bốn schema v0.1.
   Không tuyên bố multi-turn/viewer đã hoạt động. Internal history khác rỗng cần
   contract được review và retrieval lại; không âm thầm bỏ history.
4. Citation v0.1 chưa có metadata hiệu lực; không quảng bá câu trả lời là xác nhận
   pháp luật hiện hành theo ngày người dùng hỏi.
5. Root README còn link schemas cũ; alias/README ở thư mục đó giữ đường truy cập.
   Không sửa root README chung trong PR này.

## Kiểm tra diff và merge sau review

So với branch Team 2, chỉ docs/team2_rag được sửa.
So với develop, thêm sáu file thay đổi contract của PR #6 đã tồn tại trên Team 2;
không có file Team 1/3 bị sửa hoặc xóa. Phải kiểm tra lại tại thời điểm tạo/merge PR
vì các branch có thể đổi sau snapshot.

PR cá nhân → feature/team2-rag, rồi đề xuất PR → develop sau review.
Không cần main trong Week 1. Không tick Done thay thành viên hoặc tự merge.

## Evidence

- [Branches](https://github.com/Banh-Van-Hiep/vietnamese-legal-rag/branches)
- [PR #7 Team 1](https://github.com/Banh-Van-Hiep/vietnamese-legal-rag/pull/7)
- [PR #6 Contract](https://github.com/Banh-Van-Hiep/vietnamese-legal-rag/pull/6)
- [PR #4 UI](https://github.com/Banh-Van-Hiep/vietnamese-legal-rag/pull/4)
- [Team 1 retrieval tại snapshot](https://github.com/Banh-Van-Hiep/vietnamese-legal-rag/blob/83b2286f79df203cb920d1b58b84e3d2c5f7141e/docs/team1_data/retrieval-design.md)
- [Team 1 chunk tại snapshot](https://github.com/Banh-Van-Hiep/vietnamese-legal-rag/blob/83b2286f79df203cb920d1b58b84e3d2c5f7141e/docs/team1_data/chunk-format-spec.md)
- [Team 1 metadata tại snapshot](https://github.com/Banh-Van-Hiep/vietnamese-legal-rag/blob/83b2286f79df203cb920d1b58b84e3d2c5f7141e/docs/team1_data/metadata-specification.md)
- [Team 3 v1.2 tại develop](https://github.com/Banh-Van-Hiep/vietnamese-legal-rag/blob/0ce72d7f65e6e5bf59191d3139d5703e137dac41/docs/team3_fullstack/team3.md)
- [Team 3 types tại snapshot](https://github.com/Banh-Van-Hiep/vietnamese-legal-rag/blob/b6799c69110e3294132625d6110d14c95c80bc85/team3_fullstack/frontend/src/types/index.ts)
- [Team 3 API mock boundary](https://github.com/Banh-Van-Hiep/vietnamese-legal-rag/blob/b6799c69110e3294132625d6110d14c95c80bc85/team3_fullstack/frontend/src/api/chatApi.ts)
