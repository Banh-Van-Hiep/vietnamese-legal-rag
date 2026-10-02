// Một tin nhắn.
import type { ReactNode } from "react";
import type { Message } from "../../types";
import Icon from "../common/Icon";
import Seal from "../common/Seal";
import CitationList from "../citation/CitationList";

interface Props {
  message: Message;
}

export default function MessageBubble({ message }: Props) {
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
        <div className="prose">{renderContent(message.content)}</div>
        {message.citations && message.citations.length > 0 && (
          <CitationList citations={message.citations} />
        )}
        <div className="msg__actions">
          <button className="icon-btn icon-btn--sm" type="button" aria-label="Sao chép">
            <Icon name="copy" size={16} />
          </button>
          <button className="icon-btn icon-btn--sm" type="button" aria-label="Câu trả lời hữu ích">
            <Icon name="thumbUp" size={16} />
          </button>
          <button className="icon-btn icon-btn--sm" type="button" aria-label="Câu trả lời chưa tốt">
            <Icon name="thumbDown" size={16} />
          </button>
          <button className="icon-btn icon-btn--sm" type="button" aria-label="Trả lời lại">
            <Icon name="refresh" size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}

// Hiển thị văn bản tối giản: đoạn cách nhau bởi dòng trống, dòng "- " là gạch đầu dòng,
// **đậm**, và [n] là số tham chiếu tới căn cứ pháp lý.
function renderContent(content: string): ReactNode[] {
  return content.split("\n\n").map((block, i) => {
    const lines = block.split("\n");
    if (lines.every((l) => l.startsWith("- "))) {
      return (
        <ul key={i}>
          {lines.map((l, j) => (
            <li key={j}>{renderInline(l.slice(2))}</li>
          ))}
        </ul>
      );
    }
    return <p key={i}>{renderInline(block)}</p>;
  });
}

function renderInline(text: string): ReactNode[] {
  return text.split(/(\*\*[^*]+\*\*|\[\d+\])/g).map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) return <strong key={i}>{part.slice(2, -2)}</strong>;
    const ref = part.match(/^\[(\d+)\]$/);
    if (ref) return <sup key={i} className="cite-ref">{ref[1]}</sup>;
    return part;
  });
}
