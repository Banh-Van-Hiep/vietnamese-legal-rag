// Một tin nhắn. Phân biệt rõ: câu trả lời có căn cứ, thiếu căn cứ (không phải lỗi) và lỗi hệ thống.
import { useState } from "react";
import type { Citation, UiMessage } from "../../types";
import { answerWithSources } from "../../utils/legalCitation";
import Icon from "../common/Icon";
import IconButton from "../common/IconButton";
import Notice, { noticeActionClass } from "../common/Notice";
import Seal from "../common/Seal";
import CitationList from "../citation/CitationList";
import AnswerContent from "./AnswerContent";

interface Props {
  message: UiMessage;
  isLast: boolean;
  /** Căn cứ đang mở trong Viewer, chỉ tính trong tin nhắn này. */
  activeCitationId?: string | null;
  onRetry: (assistantKey: string) => void;
  onOpenCitation: (citation: Citation) => void;
}

export default function MessageBubble({ message, isLast, activeCitationId = null, onRetry, onOpenCitation }: Props) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end" data-testid="msg-user">
        <div className="max-w-[min(78%,560px)] rounded-[18px_18px_6px_18px] bg-user-bubble px-4 py-[11px] whitespace-pre-wrap">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start gap-3.5 max-[600px]:gap-2.5" data-testid="msg-assistant">
      <Seal size={30} className="mt-0.5" />
      <div className="min-w-0 flex-1">
        {message.state === "pending" && <>
          {message.content && <p className="whitespace-pre-wrap text-[15.5px] leading-[1.7]" data-testid="answer-delta">{message.content}</p>}
          <Pending />
        </>}
        {message.state === "failed" && message.failure && (
          <Notice
            variant="error"
            role="alert"
            testId="notice-error"
            title="Chưa nhận được câu trả lời"
            meta={`Mã lỗi: ${message.failure.code}${message.failure.requestId ? ` · Mã yêu cầu: ${message.failure.requestId}` : ""}`}
            action={
              message.failure.retryable && isLast ? (
                <button className={noticeActionClass} type="button" onClick={() => onRetry(message.key)}>
                  Thử lại
                </button>
              ) : undefined
            }
          >
            <p>{message.failure.message}</p>
          </Notice>
        )}
        {message.state === "completed" && message.answerStatus === "insufficient_context" && (
          <Notice
            variant="info"
            testId="notice-info"
            title="Chưa đủ căn cứ để trả lời"
            meta="Thử nêu cụ thể hơn, ví dụ tên loại hình doanh nghiệp hoặc điều khoản cần hỏi."
          >
            <p>{message.content}</p>
          </Notice>
        )}
        {message.state === "completed" && message.answerStatus !== "insufficient_context" && (
          <>
            <AnswerContent
              content={message.content ?? ""}
              citations={message.citations}
              activeCitationId={activeCitationId}
              onOpenCitation={onOpenCitation}
            />
            {message.citations.length > 0 && (
              <CitationList citations={message.citations} activeCitationId={activeCitationId} onOpen={onOpenCitation} />
            )}
            <div className="mt-2.5 -ml-1.5 flex gap-0.5">
              <CopyButton text={answerWithSources(message.content ?? "", message.citations)} />
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function Pending() {
  const dot = "size-1.5 animate-blink rounded-full bg-seal opacity-35";
  return (
    <p className="my-1 flex items-center gap-2.5 text-muted" role="status">
      <span className="inline-flex gap-1" aria-hidden="true">
        <i className={dot} />
        <i className={`${dot} [animation-delay:0.2s]`} />
        <i className={`${dot} [animation-delay:0.4s]`} />
      </span>
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
  const label = copied ? "Đã sao chép" : "Sao chép câu trả lời kèm căn cứ";
  return (
    <IconButton size="sm" className="inline-grid" onClick={copy} aria-label={label} title={label}>
      <Icon name={copied ? "check" : "copy"} size={16} />
    </IconButton>
  );
}
