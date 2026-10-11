// Khung hiển thị hội thoại.
import { useEffect, useRef } from "react";
import type { Citation, UiMessage } from "../../types";
import { suggestions } from "../../data/suggestions";
import Seal from "../common/Seal";
import MessageBubble from "./MessageBubble";

interface Props {
  messages: UiMessage[];
  loading: boolean;
  onSuggestion: (question: string) => void;
  onRetry: (assistantKey: string) => void;
  onOpenCitation: (citation: Citation) => void;
}

export default function ChatWindow({ messages, loading, onSuggestion, onRetry, onOpenCitation }: Props) {
  const end = useRef<HTMLDivElement>(null);

  useEffect(() => {
    end.current?.scrollIntoView({ block: "end" });
  }, [messages]);

  return (
    <div className="chat-scroll">
      {loading ? (
        <p className="chat-status" role="status">Đang tải hội thoại…</p>
      ) : messages.length === 0 ? (
        <Welcome onSuggestion={onSuggestion} />
      ) : (
        <div className="thread">
          {messages.map((m, i) => (
            <MessageBubble
              key={m.key}
              message={m}
              isLast={i === messages.length - 1}
              onRetry={onRetry}
              onOpenCitation={onOpenCitation}
            />
          ))}
          <div ref={end} />
        </div>
      )}
    </div>
  );
}

function Welcome({ onSuggestion }: { onSuggestion: (question: string) => void }) {
  return (
    <div className="welcome">
      <Seal size={124} withText className="welcome__seal" />
      <h2 className="welcome__title">Bạn cần hỏi gì về Luật Doanh nghiệp?</h2>
      <p className="welcome__lead">
        Hỏi về thành lập, vốn điều lệ, cổ đông, đăng ký hay giải thể doanh nghiệp. Mỗi câu trả lời
        đều kèm điều luật được trích dẫn để bạn đối chiếu.
      </p>
      <ul className="suggestions">
        {suggestions.map((s) => (
          <li key={s.question}>
            <button className="suggestion" type="button" onClick={() => onSuggestion(s.question)}>
              <span className="suggestion__field">{s.field}</span>
              <span className="suggestion__q">{s.question}</span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
