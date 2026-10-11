// Kết quả tra cứu MẪU để dựng giao diện Search. Chưa có API Search nên không có retrieval thật.
// document_id/article_id khớp fixture của MockAiClient (mock_v1/art1) để mở được viewer.
export interface SearchFixture {
  document_id: string;
  article_id: string;
  document_title: string;
  article: string;
  excerpt: string;
  /** Ghi chú hiển thị cho người thử. */
  note?: string;
}

export const searchFixtures: SearchFixture[] = [
  {
    document_id: "mock_v1",
    article_id: "art1",
    document_title: "Văn bản kiểm thử",
    article: "Điều 1",
    excerpt: "Nội dung đầy đủ của điều luật dùng để kiểm thử cấu trúc.",
  },
  {
    document_id: "mock_v1",
    article_id: "art404",
    document_title: "Văn bản kiểm thử",
    article: "Điều 404",
    excerpt: "Mục không có trong backend, dùng để thử trường hợp không tìm thấy điều luật.",
    note: "Chỉ để kiểm thử: mở mục này sẽ báo không tìm thấy.",
  },
];
