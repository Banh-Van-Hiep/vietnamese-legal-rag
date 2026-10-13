// Câu hỏi gợi ý ở màn hình chào. Bấm vào sẽ gửi câu hỏi thật tới backend.
export interface Suggestion {
  field: string;
  question: string;
}

export const suggestions: Suggestion[] = [
  { field: "Thành lập doanh nghiệp", question: "Những ai không được quyền thành lập và quản lý doanh nghiệp?" },
  { field: "Vốn điều lệ", question: "Vốn điều lệ của công ty trách nhiệm hữu hạn được xác định như thế nào?" },
  { field: "Công ty cổ phần", question: "Công ty cổ phần cần có tối thiểu bao nhiêu cổ đông?" },
  { field: "Đăng ký doanh nghiệp", question: "Hồ sơ đăng ký thành lập công ty TNHH một thành viên gồm những giấy tờ gì?" },
];
