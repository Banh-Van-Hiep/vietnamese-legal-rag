// Legal Document Viewer (VLRA-43, Docs v2.0 §8.6/§9.11–9.12, team3.md §2.4).
// Tải nguyên văn toàn Điều theo document_id/article_id của citation; tô sáng khoản/điểm được trích
// khi xác định chắc chắn vị trí; 404 vẫn cho mở nguồn chính thức của citation.
import { useEffect, useRef } from "react";
import { useArticle } from "../../hooks/useArticle";
import { citedUnitLabel, locateCitedUnit } from "../../utils/legalCitation";
import { statusTextClass } from "../common/classes";
import Icon from "../common/Icon";
import MockBadge from "../common/MockBadge";
import Notice, { noticeActionClass } from "../common/Notice";

/** Phần được trích khi mở từ một citation; không có khi mở Điều trực tiếp. */
export interface CitedFocus {
  citationId?: string | null;
  clause: string | null;
  point: string | null;
  /** source_url của citation, dùng khi nguyên văn không còn được phục vụ (404). */
  sourceUrl?: string | null;
}

interface Props {
  documentId: string;
  articleId: string;
  focus?: CitedFocus | null;
}

const externalLinkClass =
  "inline-flex items-center gap-1.5 text-seal-strong underline-offset-[3px] hover:underline";

export default function DocumentViewer({ documentId, articleId, focus = null }: Props) {
  const { state, retry } = useArticle(documentId, articleId);
  const highlight = useRef<HTMLElement>(null);
  const ready = state.status === "ready";

  useEffect(() => {
    if (ready) highlight.current?.scrollIntoView({ block: "center" });
  }, [ready, documentId, articleId, focus?.clause, focus?.point]);

  if (state.status === "loading") {
    return <p className={`${statusTextClass} !mt-6`} role="status">Đang tải nguyên văn điều luật…</p>;
  }

  if (state.status === "not_found") {
    return (
      <Notice
        variant="info"
        role="alert"
        testId="notice-info"
        title="Không mở được nguyên văn trong hệ thống"
        meta={`Mã văn bản: ${documentId} · Mã điều: ${articleId}`}
        action={
          focus?.sourceUrl ? (
            <a
              className={`${noticeActionClass} inline-flex items-center gap-1.5`}
              href={focus.sourceUrl}
              target="_blank"
              rel="noopener noreferrer"
              data-testid="fallback-source-link"
            >
              Mở nguồn văn bản chính thức
              <Icon name="externalLink" size={14} />
            </a>
          ) : undefined
        }
      >
        <p>{state.message}</p>
        <p className="mt-1 text-[13.5px] text-muted">
          Phiên bản điều luật được trích có thể không còn trong bộ dữ liệu. Câu trả lời đã lưu vẫn giữ nguyên.
        </p>
      </Notice>
    );
  }

  if (state.status === "error") {
    return (
      <Notice
        variant="error"
        role="alert"
        testId="notice-error"
        title="Chưa mở được điều luật"
        meta={state.requestId ? `Mã yêu cầu: ${state.requestId}` : undefined}
        action={<button className={noticeActionClass} type="button" onClick={retry}>Thử lại</button>}
      >
        <p>{state.message}</p>
      </Notice>
    );
  }

  const { article } = state;
  const unit = focus ? citedUnitLabel(focus) : "";
  const range = focus ? locateCitedUnit(article.content, focus.clause, focus.point) : null;

  return (
    <article>
      <header className="mb-[18px] flex flex-col items-start gap-1 border-b border-line pb-3.5">
        <p className="text-[13.5px] text-muted" data-testid="article-document">{article.document_title}</p>
        <h2 className="mb-1.5 font-serif text-[22px] leading-[1.3] font-bold text-ink-950" data-testid="article-title">
          {article.article}
        </h2>
        <MockBadge />
      </header>

      {unit && (
        <p
          className="mb-4 flex items-start gap-2 rounded-sm bg-seal-soft px-3 py-2 text-[13.5px] leading-[1.55] text-ink"
          data-testid="cited-unit"
          data-located={range !== null}
        >
          <span className="mt-0.5 flex-none text-seal"><Icon name="scale" size={15} /></span>
          <span>
            {focus?.citationId && <strong className="font-semibold">Căn cứ {focus.citationId}: </strong>}
            {unit}.{" "}
            {range
              ? "Phần được trích đã được tô sáng bên dưới."
              : "Chưa xác định chắc chắn vị trí trong nguyên văn, hãy đối chiếu toàn bộ Điều."}
          </span>
        </p>
      )}

      <div
        data-testid="article-content"
        className="font-serif text-[15.5px] leading-[1.85] [overflow-wrap:anywhere] whitespace-pre-wrap"
      >
        {range ? (
          <>
            {article.content.slice(0, range.start)}
            <mark
              ref={highlight}
              data-testid="cited-highlight"
              className="rounded-[2px] bg-[#fdf1d6] text-inherit shadow-[0_0_0_3px_#fdf1d6] [box-decoration-break:clone]"
            >
              {article.content.slice(range.start, range.end)}
            </mark>
            {article.content.slice(range.end)}
          </>
        ) : (
          article.content
        )}
      </div>

      <footer className="mt-[22px] border-t border-line pt-3 text-[13.5px]">
        <a href={article.source_url} target="_blank" rel="noopener noreferrer" data-testid="source-link" className={externalLinkClass}>
          Nguồn văn bản chính thức
          <Icon name="externalLink" size={14} />
          <span className="sr-only">(mở trong tab mới)</span>
        </a>
      </footer>
    </article>
  );
}
