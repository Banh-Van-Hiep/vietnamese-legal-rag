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

  // Tự giãn chiều cao theo nội dung, tối đa ~8 dòng (giới hạn trong CSS).
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
    <div className="composer-wrap">
      <form className="composer" onSubmit={handleSubmit}>
        <textarea
          ref={textarea}
          rows={1}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Hỏi về Luật Doanh nghiệp, ví dụ: vốn điều lệ của công ty TNHH được xác định thế nào?"
          aria-label="Câu hỏi"
          aria-invalid={tooLong}
        />
        <div className="composer__bar">
          <span className={`composer__count ${tooLong ? "is-over" : ""}`} aria-live="polite">
            {tooLong
              ? `Câu hỏi dài quá ${MAX_QUESTION_LENGTH.toLocaleString("vi-VN")} ký tự (đang ${length.toLocaleString("vi-VN")})`
              : length > MAX_QUESTION_LENGTH * 0.9
                ? `${length.toLocaleString("vi-VN")}/${MAX_QUESTION_LENGTH.toLocaleString("vi-VN")}`
                : ""}
          </span>
          <button
            className="composer__send"
            type="submit"
            disabled={!canSend}
            aria-label={sending ? "Đang chờ câu trả lời" : "Gửi câu hỏi"}
          >
            <Icon name="send" size={18} strokeWidth={2} />
          </button>
        </div>
      </form>
      <p className="composer__note">
        Câu trả lời chỉ mang tính tham khảo, không thay thế ý kiến tư vấn của luật sư.
      </p>
    </div>
  );
}
