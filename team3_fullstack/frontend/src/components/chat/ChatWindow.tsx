// Khung hiển thị hội thoại.
import { useEffect, useRef } from "react";
import type { Citation, UiMessage } from "../../types";
import { suggestions } from "../../data/suggestions";
import { statusTextClass } from "../common/classes";
import Seal from "../common/Seal";
import ScopeNote from "../common/ScopeNote";
import MessageBubble from "./MessageBubble";

interface Props {
  messages: UiMessage[];
  loading: boolean;
  onSuggestion: (question: string) => void;
  onRetry: (assistantKey: string) => void;
  /** Căn cứ đang mở trong Viewer: key của tin assistant và citation_id. */
  openCitation?: { messageKey: string; citationId: string } | null;
  onOpenCitation: (messageKey: string, citation: Citation) => void;
}

export default function ChatWindow({ messages, loading, onSuggestion, onRetry, openCitation = null, onOpenCitation }: Props) {
  const end = useRef<HTMLDivElement>(null);

  useEffect(() => {
    end.current?.scrollIntoView({ block: "end" });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto px-6 max-[600px]:px-4">
      {loading ? (
        <p className={statusTextClass} role="status">Đang tải hội thoại…</p>
      ) : messages.length === 0 ? (
        <Welcome onSuggestion={onSuggestion} />
      ) : (
        <div className="mx-auto flex max-w-[760px] flex-col gap-7 pt-8 pb-6">
          {messages.map((m, i) => (
            <MessageBubble
              key={m.key}
              message={m}
              isLast={i === messages.length - 1}
              activeCitationId={openCitation?.messageKey === m.key ? openCitation.citationId : null}
              onRetry={onRetry}
              onOpenCitation={(citation) => onOpenCitation(m.key, citation)}
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
    <div className="mx-auto max-w-[680px] pt-[9vh] pb-8 text-center">
      <Seal size={124} withText className="mx-auto mb-7 block animate-stamp" />
      <h2 className="font-serif text-[clamp(26px,4vw,34px)] leading-[1.25] font-semibold tracking-[-0.01em] text-ink-950">
        Bạn cần hỏi gì về Luật Doanh nghiệp?
      </h2>
      <p className="mx-auto mt-3 mb-8 max-w-[52ch] text-muted">
        Hỏi về thành lập, vốn điều lệ, cổ đông, đăng ký hay giải thể doanh nghiệp. Mỗi câu trả lời
        đều kèm điều luật được trích dẫn để bạn đối chiếu.
      </p>
      <ul className="grid grid-cols-2 gap-2.5 text-left max-[600px]:grid-cols-1">
        {suggestions.map((s) => (
          <li key={s.question}>
            <button
              type="button"
              data-testid="suggestion"
              onClick={() => onSuggestion(s.question)}
              className="flex h-full w-full flex-col gap-1 rounded-xl border border-line bg-surface px-4 py-3.5 text-left hover:border-line-strong hover:bg-paper"
            >
              <span className="text-[12.5px] font-semibold text-seal">{s.field}</span>
              <span className="text-[14.5px] leading-[1.45] text-ink">{s.question}</span>
            </button>
          </li>
        ))}
      </ul>
      <ScopeNote className="mt-7" />
    </div>
  );
}
