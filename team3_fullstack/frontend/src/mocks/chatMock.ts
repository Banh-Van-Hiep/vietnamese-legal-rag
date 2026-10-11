// Dữ liệu mẫu để dựng giao diện khi chưa nối backend. Không dùng cho tư vấn thật.
import type { Conversation, Message } from "../types";

export interface ConversationGroup {
  label: string;
  items: Conversation[];
}

export const mockConversationGroups: ConversationGroup[] = [
  {
    label: "Hôm nay",
    items: [
      { id: 1, title: "Thời gian nghỉ thai sản" },
      { id: 2, title: "Công ty chậm trả lương" },
    ],
  },
  {
    label: "7 ngày qua",
    items: [
      { id: 3, title: "Thời hạn hợp đồng thử việc" },
      { id: 4, title: "Trợ cấp thôi việc khi nghỉ việc" },
      { id: 5, title: "Giới hạn giờ làm thêm" },
    ],
  },
  {
    label: "Tháng trước",
    items: [
      { id: 6, title: "Đơn phương chấm dứt hợp đồng" },
      { id: 7, title: "Phép năm chưa nghỉ hết" },
    ],
  },
];

export interface Suggestion {
  field: string;
  question: string;
}

export const mockSuggestions: Suggestion[] = [
  { field: "Hợp đồng lao động", question: "Hợp đồng thử việc được kéo dài tối đa bao lâu?" },
  { field: "Tiền lương", question: "Công ty chậm trả lương thì người lao động được bồi thường thế nào?" },
  { field: "Thời giờ làm việc", question: "Một năm được làm thêm giờ tối đa bao nhiêu giờ?" },
  { field: "Chấm dứt hợp đồng", question: "Tự nghỉ việc thì phải báo trước cho công ty bao nhiêu ngày?" },
];

const BLLD = "Bộ luật Lao động 2019 (số 45/2019/QH14)";

export const mockMessages: Message[] = [
  {
    id: 1,
    role: "user",
    content:
      "Lao động nữ được nghỉ thai sản bao lâu? Công ty có được cho tôi nghỉ việc khi tôi đang mang thai không?",
  },
  {
    id: 2,
    role: "assistant",
    content: [
      "Theo Bộ luật Lao động 2019, câu hỏi của bạn liên quan đến hai quy định:",
      "**Thời gian nghỉ thai sản**",
      [
        "- Lao động nữ được nghỉ thai sản **6 tháng** cả trước và sau khi sinh con [1].",
        "- Thời gian nghỉ trước khi sinh tối đa **2 tháng**.",
        "- Sinh đôi trở lên: từ con thứ hai, mỗi con được nghỉ thêm 1 tháng.",
      ].join("\n"),
      "**Công ty không được cho bạn nghỉ việc vì lý do mang thai**",
      "Người sử dụng lao động không được sa thải hoặc đơn phương chấm dứt hợp đồng với người lao động vì lý do kết hôn, mang thai, nghỉ thai sản hoặc nuôi con dưới 12 tháng tuổi, trừ một số trường hợp như doanh nghiệp chấm dứt hoạt động [2].",
      "Nếu công ty vẫn cho bạn nghỉ việc, bạn có thể gửi khiếu nại tới công đoàn cơ sở, thanh tra lao động, hoặc khởi kiện tại Tòa án.",
    ].join("\n\n"),
    citations: [
      {
        chunkId: "blld-2019-d139-k1",
        documentTitle: BLLD,
        article: "Điều 139. Nghỉ thai sản",
        snippet:
          "1. Lao động nữ được nghỉ thai sản trước và sau khi sinh con là 06 tháng; thời gian nghỉ trước khi sinh tối đa không quá 02 tháng. Trường hợp lao động nữ sinh đôi trở lên thì tính từ con thứ 02 trở đi, cứ mỗi con, người mẹ được nghỉ thêm 01 tháng.",
      },
      {
        chunkId: "blld-2019-d137-k3",
        documentTitle: BLLD,
        article: "Điều 137. Bảo vệ thai sản",
        snippet:
          "3. Người sử dụng lao động không được sa thải hoặc đơn phương chấm dứt hợp đồng lao động đối với người lao động vì lý do kết hôn, mang thai, nghỉ thai sản, nuôi con dưới 12 tháng tuổi, trừ trường hợp người sử dụng lao động là cá nhân chết, bị Tòa án tuyên bố mất năng lực hành vi dân sự, mất tích hoặc là đã chết hoặc người sử dụng lao động không phải là cá nhân chấm dứt hoạt động…",
      },
    ],
  },
  {
    id: 3,
    role: "user",
    content: "Trong thời gian nghỉ thai sản tôi có được trả lương không?",
  },
  {
    id: 4,
    role: "assistant",
    content: [
      "Trong thời gian nghỉ thai sản, bạn không nhận lương từ công ty mà được hưởng **chế độ thai sản từ quỹ bảo hiểm xã hội** [1], với điều kiện đã đóng bảo hiểm xã hội đủ thời gian theo quy định.",
      "Mức hưởng và điều kiện cụ thể nằm trong Luật Bảo hiểm xã hội. Bạn nên hỏi bộ phận nhân sự hoặc cơ quan bảo hiểm xã hội nơi đang đóng để biết số tiền chính xác.",
    ].join("\n\n"),
    citations: [
      {
        chunkId: "blld-2019-d139-k4",
        documentTitle: BLLD,
        article: "Điều 139. Nghỉ thai sản",
        snippet:
          "4. Trong thời gian nghỉ thai sản theo quy định tại Điều này, lao động nữ được hưởng chế độ thai sản theo quy định của pháp luật về bảo hiểm xã hội.",
      },
    ],
  },
];

export function findConversationTitle(id?: number): string | undefined {
  return mockConversationGroups.flatMap((g) => g.items).find((c) => c.id === id)?.title;
}
