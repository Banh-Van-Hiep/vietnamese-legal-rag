// Hiển thị nguyên văn điều luật theo ID. Dùng cho cả ngăn trượt trong Chat và trang riêng.
import { useArticle } from "../../hooks/useArticle";
import { statusTextClass } from "../common/classes";
import Icon from "../common/Icon";
import MockBadge from "../common/MockBadge";
import Notice, { noticeActionClass } from "../common/Notice";

interface Props {
  documentId: string;
  articleId: string;
}

export default function DocumentViewer({ documentId, articleId }: Props) {
  const { state, retry } = useArticle(documentId, articleId);

  if (state.status === "loading") {
    return <p className={`${statusTextClass} !mt-6`} role="status">Đang tải điều luật…</p>;
  }

  if (state.status === "not_found") {
    return (
      <Notice
        variant="info"
        role="alert"
        testId="notice-info"
        title="Không tìm thấy điều luật"
        meta={`Mã văn bản: ${documentId} · Mã điều: ${articleId}`}
      >
        <p>{state.message}</p>
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
  return (
    <article>
      <header className="mb-[18px] flex flex-col items-start gap-1 border-b border-line pb-3.5">
        <p className="text-[13.5px] text-muted">{article.document_title}</p>
        <h2 className="mb-1.5 font-serif text-[22px] leading-[1.3] font-bold text-ink-950" data-testid="article-title">
          {article.article}
        </h2>
        <MockBadge />
      </header>
      <div
        data-testid="article-content"
        className="font-serif text-[15.5px] leading-[1.85] [overflow-wrap:anywhere] whitespace-pre-wrap hyphens-auto text-justify"
      >
        {article.content}
      </div>
      <footer className="mt-[22px] border-t border-line pt-3 text-[13.5px]">
        <a
          href={article.source_url}
          target="_blank"
          rel="noopener noreferrer"
          data-testid="source-link"
          className="inline-flex items-center gap-1.5 text-seal-strong underline-offset-[3px] hover:underline"
        >
          Nguồn văn bản
          <Icon name="externalLink" size={14} />
        </a>
      </footer>
    </article>
  );
}
