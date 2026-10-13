// Một trích dẫn. Nội dung điều luật được tải theo ID khi người dùng mở, không nhúng sẵn trong câu trả lời.
import type { Citation } from "../../types";
import { cardClass, openLinkClass } from "../common/classes";

interface Props {
  citation: Citation;
  onOpen: (citation: Citation) => void;
}

export default function CitationCard({ citation, onOpen }: Props) {
  const location = [citation.article, citation.clause, citation.point].filter(Boolean).join(", ");
  return (
    <article className={cardClass} data-testid="citation">
      <header className="flex items-start gap-3">
        <span className="mt-px inline-grid size-[22px] flex-none place-items-center rounded-[4px] bg-seal-soft text-[12px] font-semibold text-seal-strong">
          {citation.citation_id.replace(/^C/, "")}
        </span>
        <div>
          <h3 className="font-serif text-[15.5px] leading-[1.4] font-bold text-ink-950">{location}</h3>
          <p className="mt-0.5 text-[13px] text-muted">{citation.document_title}</p>
        </div>
      </header>
      <button
        type="button"
        data-testid="open-article"
        onClick={() => onOpen(citation)}
        className={`${openLinkClass} mt-2 ml-[34px] max-[600px]:ml-0`}
      >
        Xem nguyên văn điều luật
      </button>
    </article>
  );
}
