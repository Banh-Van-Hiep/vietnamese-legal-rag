// Con dấu đỏ: nhận diện của trợ lý. Bản lớn có chữ chạy quanh vành, bản nhỏ dùng làm avatar.
import { useId } from "react";
import Icon from "./Icon";

interface Props {
  size?: number;
  withText?: boolean;
  /** "dark": bản nhỏ đặt trên nền thanh bên xanh đậm. */
  tone?: "light" | "dark";
  className?: string;
}

const small = {
  light:
    "bg-surface text-seal shadow-[inset_0_0_0_2px_var(--color-surface),inset_0_0_0_2.75px_currentColor]",
  dark:
    "bg-transparent text-seal-light shadow-[inset_0_0_0_2px_var(--color-ink-900),inset_0_0_0_2.75px_currentColor]",
};

export default function Seal({ size = 32, withText = false, tone = "light", className = "" }: Props) {
  const pathId = useId();

  if (!withText) {
    return (
      <span
        className={`inline-grid flex-none place-items-center rounded-full border-[1.5px] border-current ${small[tone]} ${className}`}
        style={{ width: size, height: size }}
      >
        <Icon name="scale" size={Math.round(size * 0.56)} strokeWidth={1.6} />
      </span>
    );
  }

  return (
    <svg
      className={`flex-none text-seal ${className}`}
      width={size}
      height={size}
      viewBox="0 0 120 120"
      role="img"
      aria-label="Con dấu Legal AI"
    >
      <circle cx="60" cy="60" r="56" fill="none" stroke="currentColor" strokeWidth="3" />
      <circle cx="60" cy="60" r="50" fill="none" stroke="currentColor" strokeWidth="1" />
      <circle cx="60" cy="60" r="33" fill="none" stroke="currentColor" strokeWidth="1" />
      <defs>
        <path id={pathId} d="M60 60m-41.5 0a41.5 41.5 0 1 1 83 0a41.5 41.5 0 1 1-83 0" />
      </defs>
      <text className="font-serif text-[9.6px] font-semibold tracking-[0.9px]" fill="currentColor">
        <textPath href={`#${pathId}`} textLength="256" lengthAdjust="spacing">
          LUẬT DOANH NGHIỆP ★ LEGAL AI ★ VIỆT NAM ★
        </textPath>
      </text>
      <g transform="translate(42 42) scale(1.5)">
        <Icon name="scale" size={24} strokeWidth={1.4} />
      </g>
    </svg>
  );
}
