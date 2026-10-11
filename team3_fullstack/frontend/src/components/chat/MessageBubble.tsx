// Một tin nhắn. Phân biệt rõ: câu trả lời có căn cứ, thiếu căn cứ (không phải lỗi) và lỗi hệ thống.
import { useState, type ReactNode } from "react";
import type { Citation, UiMessage } from "../../types";
import Icon from "../common/Icon";
import Seal from "../common/Seal";
import CitationList from "../citation/CitationList";

interface Props {
  message: UiMessage;
  isLast: boolean;
  onRetry: (assistantKey: string) => void;
  onOpenCitation: (citation: Citation) => void;
}

export default function MessageBubble({ message, isLast, onRetry, onOpenCitation }: Props) {
  if (message.role === "user") {
    return (
      <div className="msg msg--user">
        <div className="msg__bubble">{message.content}</div>
      </div>
    );
  }

  return (
    <div className="msg msg--assistant">
      <Seal size={30} className="msg__avatar" />
      <div className="msg__body">
        {message.state === "pending" && <Pending />}
        {message.state === "failed" && message.failure && (
          <div className="notice notice--error" role="alert">
            <Icon name="alert" size={18} />
            <div>
              <p className="notice__title">Chưa nhận được câu trả lời</p>
              <p>{message.failure.message}</p>
              <p className="notice__meta">
                Mã lỗi: {message.failure.code}
                {message.failure.requestId ? ` · Mã yêu cầu: ${message.failure.requestId}` : ""}
              </p>
              {message.failure.retryable && isLast && (
                <button className="notice__action" type="button" onClick={() => onRetry(message.key)}>
                  Thử lại
                </button>
              )}
            </div>
          </div>
        )}
        {message.state === "completed" && message.answerStatus === "insufficient_context" && (
          <div className="notice notice--info">
            <Icon name="info" size={18} />
            <div>
              <p className="notice__title">Chưa đủ căn cứ để trả lời</p>
              <p>{message.content}</p>
              <p className="notice__meta">Thử nêu cụ thể hơn, ví dụ tên loại hình doanh nghiệp hoặc điều khoản cần hỏi.</p>
            </div>
          </div>
        )}
        {message.state === "completed" && message.answerStatus !== "insufficient_context" && (
          <>
            <div className="prose">{renderContent(message.content ?? "", message.citations, onOpenCitation)}</div>
            {message.citations.length > 0 && (
              <CitationList citations={message.citations} onOpen={onOpenCitation} />
            )}
            <div className="msg__actions">
              <CopyButton text={message.content ?? ""} />
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function Pending() {
  return (
    <p className="pending" role="status">
      <span className="pending__dots" aria-hidden="true"><i /><i /><i /></span>
      Đang tra cứu căn cứ pháp lý…
    </p>
  );
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* Trình duyệt chặn clipboard: bỏ qua, người dùng vẫn chọn và sao chép tay được. */
    }
  }
  return (
    <button className="icon-btn icon-btn--sm" type="button" onClick={copy} aria-label={copied ? "Đã sao chép" : "Sao chép câu trả lời"}>
      <Icon name={copied ? "check" : "copy"} size={16} />
    </button>
  );
}

// Hiển thị văn bản tối giản: đoạn cách nhau bởi dòng trống, dòng "- " là gạch đầu dòng,
// **đậm**, và [C1] là dấu tham chiếu tới căn cứ pháp lý (bấm để mở nguyên văn).
function renderContent(content: string, citations: Citation[], onOpen: (c: Citation) => void): ReactNode[] {
  return content.split("\n\n").map((block, i) => {
    const lines = block.split("\n");
    if (lines.every((l) => l.startsWith("- "))) {
      return (
        <ul key={i}>
          {lines.map((l, j) => (
            <li key={j}>{renderInline(l.slice(2), citations, onOpen)}</li>
          ))}
        </ul>
      );
    }
    return <p key={i}>{renderInline(block, citations, onOpen)}</p>;
  });
}

function renderInline(text: string, citations: Citation[], onOpen: (c: Citation) => void): ReactNode[] {
  return text.split(/(\*\*[^*]+\*\*|\[C\d+\])/g).map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) return <strong key={i}>{part.slice(2, -2)}</strong>;
    const marker = part.match(/^\[(C\d+)\]$/);
    if (marker) {
      const citation = citations.find((c) => c.citation_id === marker[1]);
      if (!citation) return part;
      return (
        <button
          key={i}
          type="button"
          className="cite-ref"
          onClick={() => onOpen(citation)}
          aria-label={`Mở căn cứ ${citation.citation_id}: ${citation.article}`}
        >
          {marker[1].slice(1)}
        </button>
      );
    }
    return part;
  });
}
