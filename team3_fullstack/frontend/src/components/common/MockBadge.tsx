// Nhận diện dữ liệu thử nghiệm. Tắt bằng VITE_MOCK_MODE=false khi backend dùng dữ liệu thật.
import Icon from "./Icon";

export const isMockMode = import.meta.env.VITE_MOCK_MODE !== "false";

export default function MockBadge() {
  if (!isMockMode) return null;
  return (
    <span
      data-testid="mock-badge"
      className="inline-flex flex-none items-center gap-1.5 rounded-full border border-dashed border-mock-border bg-mock-bg py-[3px] pr-2.5 pl-2 text-[12.5px] font-medium whitespace-nowrap text-mock-ink"
      title="Backend đang trả dữ liệu mẫu để kiểm thử cấu trúc. Đây không phải nội dung pháp luật thật."
    >
      <Icon name="info" size={14} />
      Dữ liệu thử nghiệm
    </span>
  );
}
