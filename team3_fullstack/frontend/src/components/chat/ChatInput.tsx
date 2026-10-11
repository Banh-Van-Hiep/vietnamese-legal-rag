// Ô nhập câu hỏi: chặn câu hỏi rỗng và gửi trùng khi đang chờ trả lời.
import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import { MAX_QUESTION_LENGTH } from "../../hooks/useChat";
import { codePointLength } from "../../utils/text";
import Icon from "../common/Icon";

interface Props {
  /** Trả về true nếu câu hỏi được nhận. */
  onSend: (question: string) => boolean;
  sending: boolean;
}

export default function ChatInput({ onSend, sending }: Props) {
  const [value, setValue] = useState("");
  const textarea = useRef<HTMLTextAreaElement>(null);

  const length = codePointLength(value.trim());
  const tooLong = length > MAX_QUESTION_LENGTH;
  const canSend = length > 0 && !tooLong && !sending;

  // Tự giãn chiều cao theo nội dung, tối đa ~8 dòng (max-h trên textarea).
  useEffect(() => {
    const el = textarea.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight}px`;
  }, [value]);

  // Trả lại con trỏ cho ô nhập khi câu trả lời về.
  useEffect(() => {
    if (!sending) textarea.current?.focus();
  }, [sending]);

  function submit() {
    if (!canSend) return;
    if (onSend(value)) setValue("");
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    submit();
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      submit();
    }
  }

  return (
    <div className="flex-none px-6 pt-2 pb-3.5 max-[600px]:px-4">
      <form
        onSubmit={handleSubmit}
        className="mx-auto max-w-[760px] rounded-2xl border border-line-strong bg-surface shadow-[0_1px_2px_rgba(18,27,46,0.04),0_6px_24px_-12px_rgba(18,27,46,0.18)] transition-colors duration-[120ms] focus-within:border-ink-700"
      >
        <textarea
          ref={textarea}
          rows={1}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Hỏi về Luật Doanh nghiệp, ví dụ: vốn điều lệ của công ty TNHH được xác định thế nào?"
          aria-label="Câu hỏi"
          aria-invalid={tooLong}
          className="block max-h-[216px] w-full resize-none border-0 bg-transparent px-[18px] pt-3.5 pb-1 text-[15.5px] leading-[1.6] outline-0 placeholder:text-faint"
        />
        <div className="flex items-center justify-between pt-1.5 pr-2 pb-2 pl-2.5">
          <span
            data-testid="char-count"
            data-over={tooLong}
            aria-live="polite"
            className={`pl-2.5 text-[13px] ${tooLong ? "font-medium text-seal-strong" : "text-muted"}`}
          >
            {tooLong
              ? `Câu hỏi dài quá ${MAX_QUESTION_LENGTH.toLocaleString("vi-VN")} ký tự (đang ${length.toLocaleString("vi-VN")})`
              : length > MAX_QUESTION_LENGTH * 0.9
                ? `${length.toLocaleString("vi-VN")}/${MAX_QUESTION_LENGTH.toLocaleString("vi-VN")}`
                : ""}
          </span>
          <button
            type="submit"
            data-testid="send"
            disabled={!canSend}
            aria-label={sending ? "Đang chờ câu trả lời" : "Gửi câu hỏi"}
            className="inline-grid size-9 place-items-center rounded-[10px] bg-ink-900 text-white hover:enabled:bg-ink-700 disabled:cursor-not-allowed disabled:bg-line disabled:text-faint"
          >
            <Icon name="send" size={18} strokeWidth={2} />
          </button>
        </div>
      </form>
      <p className="mt-2 text-center text-[12.5px] text-faint">
        Câu trả lời chỉ mang tính tham khảo, không thay thế ý kiến tư vấn của luật sư.
      </p>
    </div>
  );
}
