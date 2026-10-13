// Nút bấm chỉ có icon. Người gọi tự đặt display (inline-grid, hoặc ẩn/hiện theo màn hình) qua className.
import { forwardRef, type ButtonHTMLAttributes } from "react";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  size?: "md" | "sm";
  /** "dark": dùng trên nền thanh bên màu xanh đậm. */
  tone?: "light" | "dark";
}

const sizes = { md: "size-9", sm: "size-[30px]" };
const tones = {
  light: "text-muted hover:bg-ink/6 hover:text-ink",
  dark: "text-side-muted hover:bg-white/6 hover:text-white",
};

const IconButton = forwardRef<HTMLButtonElement, Props>(function IconButton(
  { size = "md", tone = "light", className = "", type = "button", ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      type={type}
      className={`place-items-center rounded-lg ${sizes[size]} ${tones[tone]} ${className}`}
      {...rest}
    />
  );
});

export default IconButton;
