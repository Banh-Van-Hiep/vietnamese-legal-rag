// Nội dung câu trả lời có căn cứ (VLRA-43). Chỉ render cấu trúc đã phân tích ở utils/answerFormat;
// dấu [Cn] thành nút mở đúng citation trong array đã kiểm tra, không lấy ID từ văn bản LLM.
import type { ReactNode } from "react";
import type { Citation } from "../../types";
import { parseAnswer, type Inline } from "../../utils/answerFormat";
import { citationLocation } from "../../utils/legalCitation";

interface Props {
  content: string;
  citations: Citation[];
  activeCitationId?: string | null;
  onOpenCitation: (citation: Citation) => void;
}

export default function AnswerContent({ content, citations, activeCitationId, onOpenCitation }: Props) {
  const inline = (parts: Inline[]) => renderInline(parts, citations, activeCitationId ?? null, onOpenCitation);
  return (
    <div className="text-[15.5px] leading-[1.7] [overflow-wrap:anywhere]" data-testid="answer">
      {parseAnswer(content).map((block, i) => {
        switch (block.kind) {
          case "heading":
            return (
              <p key={i} className="mt-[18px] mb-1.5 font-semibold text-ink-950 first:mt-0">
                {block.text}
              </p>
            );
          case "bullets":
            return (
              <ul key={i} className="mb-3.5 list-disc pl-[22px]">
                {block.items.map((item, j) => (
                  <li key={j} className="mb-1 marker:text-faint">{inline(item)}</li>
                ))}
              </ul>
            );
          case "numbered":
            return (
              <ol key={i} className="mb-3.5 flex list-none flex-col gap-1 pl-0">
                {block.items.map((item, j) => (
                  <li key={j} className="grid grid-cols-[auto_1fr] gap-x-2">
                    <span className="min-w-[1.4em] text-right text-muted tabular-nums">{item.marker}</span>
                    <span>{inline(item.content)}</span>
                  </li>
                ))}
              </ol>
            );
          default:
            return (
              <p key={i} className="mb-3">
                {block.lines.map((line, j) => (
                  <span key={j}>
                    {j > 0 && <br />}
                    {inline(line)}
                  </span>
                ))}
              </p>
            );
        }
      })}
    </div>
  );
}

function renderInline(
  parts: Inline[],
  citations: Citation[],
  activeCitationId: string | null,
  onOpen: (citation: Citation) => void,
): ReactNode[] {
  return parts.map((part, i) => {
    if (part.kind === "bold") {
      return <strong key={i} className="font-semibold text-ink-950">{part.text}</strong>;
    }
    if (part.kind === "text") return part.text;
    const citation = citations.find((c) => c.citation_id === part.citationId);
    if (!citation) return `[${part.citationId}]`;
    const location = citationLocation(citation);
    const active = citation.citation_id === activeCitationId;
    return (
      <button
        key={i}
        type="button"
        data-testid="cite-ref"
        data-active={active}
        onClick={() => onOpen(citation)}
        title={`${location} — ${citation.document_title}`}
        aria-label={`Mở căn cứ ${citation.citation_id}: ${location}, ${citation.document_title}`}
        className={`ml-0.5 inline-grid h-[18px] min-w-[18px] place-items-center rounded-[4px] px-1 align-[3px] text-[11px] leading-none font-semibold focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-focus ${
          active ? "bg-seal text-white" : "bg-seal-soft text-seal-strong hover:bg-seal-line"
        }`}
      >
        {citation.citation_id.replace(/^C/, "")}
      </button>
    );
  });
}
