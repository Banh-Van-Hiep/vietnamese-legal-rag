// Hiển thị nguyên văn điều luật theo ID. Dùng cho cả ngăn trượt trong Chat và trang riêng.
import { useArticle } from "../../hooks/useArticle";
import Icon from "../common/Icon";
import MockBadge from "../common/MockBadge";

interface Props {
  documentId: string;
  articleId: string;
}

export default function DocumentViewer({ documentId, articleId }: Props) {
  const { state, retry } = useArticle(documentId, articleId);

  if (state.status === "loading") {
    return <p className="chat-status" role="status">Đang tải điều luật…</p>;
  }

  if (state.status === "not_found") {
    return (
      <div className="notice notice--info" role="alert">
        <Icon name="info" size={18} />
        <div>
          <p className="notice__title">Không tìm thấy điều luật</p>
          <p>{state.message}</p>
          <p className="notice__meta">Mã văn bản: {documentId} · Mã điều: {articleId}</p>
        </div>
      </div>
    );
  }

  if (state.status === "error") {
    return (
      <div className="notice notice--error" role="alert">
        <Icon name="alert" size={18} />
        <div>
          <p className="notice__title">Chưa mở được điều luật</p>
          <p>{state.message}</p>
          {state.requestId && <p className="notice__meta">Mã yêu cầu: {state.requestId}</p>}
          <button className="notice__action" type="button" onClick={retry}>Thử lại</button>
        </div>
      </div>
    );
  }

  const { article } = state;
  return (
    <article className="viewer">
      <header className="viewer__head">
        <p className="viewer__doc">{article.document_title}</p>
        <h2 className="viewer__article">{article.article}</h2>
        <MockBadge />
      </header>
      <div className="viewer__content">{article.content}</div>
      <footer className="viewer__source">
        <a href={article.source_url} target="_blank" rel="noopener noreferrer">
          Nguồn văn bản
          <Icon name="externalLink" size={14} />
        </a>
      </footer>
    </article>
  );
}
