// Ngăn trượt bên phải để xem điều luật mà vẫn giữ nguyên hội thoại phía sau.
import { useEffect, useRef } from "react";
import type { Citation } from "../../types";
import Icon from "../common/Icon";
import DocumentViewer from "./DocumentViewer";

interface Props {
  citation: Citation;
  onClose: () => void;
}

export default function DocumentDrawer({ citation, onClose }: Props) {
  const closeButton = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    closeButton.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <>
      <div className="drawer-backdrop" onClick={onClose} />
      <aside className="drawer" role="dialog" aria-label={`Nguyên văn ${citation.article}`}>
        <div className="drawer__bar">
          <span className="drawer__title">Nguyên văn điều luật</span>
          <button ref={closeButton} className="icon-btn" type="button" onClick={onClose} aria-label="Đóng">
            <Icon name="close" />
          </button>
        </div>
        <div className="drawer__body">
          <DocumentViewer documentId={citation.document_id} articleId={citation.article_id} />
        </div>
      </aside>
    </>
  );
}
