// Một trích dẫn (Docs v2.0 §8.6): số Cn, văn bản, Điều/Khoản/Điểm và link nguồn.
// Nguyên văn điều luật chỉ được tải khi người dùng mở, theo document_id/article_id của chính citation.
import type { Citation } from "../../types";
import { citationLocation } from "../../utils/legalCitation";
import { openLinkClass } from "../common/classes";
import Icon from "../common/Icon";

interface Props {
  citation: Citation;
  active?: boolean;
  onOpen: (citation: Citation) => void;
}

export default function CitationCard({ citation, active = false, onOpen }: Props) {
  const number = citation.citation_id.replace(/^C/, "");
  return (
    <article
      data-testid="citation"
      data-active={active}
      aria-current={active ? "true" : undefined}
      className={`rounded-sm border border-l-[3px] px-[18px] pt-3.5 pb-2.5 transition-colors max-[600px]:px-3.5 ${
        active ? "border-seal-line border-l-seal bg-seal-soft" : "border-line border-l-seal bg-paper"
      }`}
    >
      <header className="flex items-start gap-3">
        <span
          aria-label={`Căn cứ ${citation.citation_id}`}
          className={`mt-px inline-grid size-[22px] flex-none place-items-center rounded-[4px] text-[12px] font-semibold ${
            active ? "bg-seal text-white" : "bg-seal-soft text-seal-strong"
          }`}
        >
          {number}
        </span>
        <div className="min-w-0">
          <h3 className="font-serif text-[15.5px] leading-[1.4] font-bold text-ink-950" data-testid="citation-location">
            {citationLocation(citation)}
          </h3>
          <p className="mt-0.5 text-[13px] text-muted [overflow-wrap:anywhere]">{citation.document_title}</p>
        </div>
      </header>
      <div className="mt-1.5 ml-[34px] flex flex-wrap items-center gap-x-3 gap-y-0.5 max-[600px]:ml-0">
        <button type="button" data-testid="open-article" onClick={() => onOpen(citation)} className={openLinkClass}>
          Xem nguyên văn
        </button>
        <a
          href={citation.source_url}
          target="_blank"
          rel="noopener noreferrer"
          data-testid="citation-source"
          className={`${openLinkClass} inline-flex items-center gap-1 !text-muted hover:!text-seal-strong`}
        >
          Nguồn chính thức
          <Icon name="externalLink" size={13} />
          <span className="sr-only">(mở trong tab mới)</span>
        </a>
      </div>
    </article>
  );
}
