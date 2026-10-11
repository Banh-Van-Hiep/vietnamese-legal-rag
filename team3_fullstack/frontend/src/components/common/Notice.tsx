// Khung thông báo: lỗi (đỏ) hoặc thông tin (xanh), dùng cho lỗi hệ thống, thiếu căn cứ, không tìm thấy.
import type { ReactNode } from "react";
import Icon from "./Icon";

interface Props {
  variant: "error" | "info";
  title: string;
  children?: ReactNode;
  /** Dòng phụ nhỏ, màu nhạt: mã lỗi, mã yêu cầu… */
  meta?: ReactNode;
  action?: ReactNode;
  className?: string;
  role?: "alert" | "status";
  testId?: string;
}

const variants = {
  error: { box: "border-seal-line border-l-seal bg-seal-soft", icon: "text-seal" },
  info: { box: "border-line border-l-ink-700 bg-paper", icon: "text-ink-700" },
};

/** Nút/liên kết hành động đặt trong Notice, ví dụ "Thử lại". */
export const noticeActionClass =
  "mt-2.5 inline-block rounded-lg border border-ink-700 bg-surface px-3.5 py-1.5 text-[13.5px] font-medium text-ink-900 hover:bg-paper";

export default function Notice({ variant, title, children, meta, action, className = "", role, testId }: Props) {
  return (
    <div
      role={role}
      data-testid={testId}
      className={`flex items-start gap-3 rounded-sm border border-l-[3px] px-4 py-3.5 text-[14.5px] leading-[1.6] text-ink ${variants[variant].box} ${className}`}
    >
      <span className={`mt-0.5 flex-none ${variants[variant].icon}`}>
        <Icon name={variant === "error" ? "alert" : "info"} size={18} />
      </span>
      <div>
        <p className="mb-0.5 font-semibold">{title}</p>
        {children}
        {meta && <p className="mt-1.5 text-[12.5px] text-muted [overflow-wrap:anywhere]">{meta}</p>}
        {action}
      </div>
    </div>
  );
}
