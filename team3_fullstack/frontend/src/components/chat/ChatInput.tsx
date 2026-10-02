// Ô nhập câu hỏi. Hiện chỉ là giao diện: gửi chưa làm gì.
import { useEffect, useRef, useState, type FormEvent } from "react";
import Icon from "../common/Icon";

export default function ChatInput() {
  const [value, setValue] = useState("");
  const textarea = useRef<HTMLTextAreaElement>(null);

  // Tự giãn chiều cao theo nội dung, tối đa ~8 dòng (giới hạn trong CSS).
  useEffect(() => {
    const el = textarea.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight}px`;
  }, [value]);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
  }

  return (
    <div className="composer-wrap">
      <form className="composer" onSubmit={handleSubmit}>
        <textarea
          ref={textarea}
          rows={1}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Hỏi về luật lao động, ví dụ: bị cho nghỉ việc không báo trước thì được bồi thường gì?"
          aria-label="Câu hỏi"
        />
        <div className="composer__bar">
          <button className="composer__tool" type="button">
            <Icon name="attach" size={16} />
            Đính kèm văn bản
          </button>
          <button className="composer__send" type="submit" disabled={!value.trim()} aria-label="Gửi câu hỏi">
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
