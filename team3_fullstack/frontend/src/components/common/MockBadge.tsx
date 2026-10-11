// Nhận diện dữ liệu thử nghiệm. Tắt bằng VITE_MOCK_MODE=false khi backend dùng dữ liệu thật.
import Icon from "./Icon";

export const isMockMode = import.meta.env.VITE_MOCK_MODE !== "false";

export default function MockBadge() {
  if (!isMockMode) return null;
  return (
    <span
      className="mock-badge"
      title="Backend đang trả dữ liệu mẫu để kiểm thử cấu trúc. Đây không phải nội dung pháp luật thật."
    >
      <Icon name="info" size={14} />
      Dữ liệu thử nghiệm
    </span>
  );
}
