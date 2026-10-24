// Ngăn trượt bên phải để xem nguyên văn mà vẫn giữ nguyên hội thoại phía sau (Docs v2.0 §8.6).
// Hộp thoại modal: giữ focus bên trong, Escape để đóng và trả focus về nút đã mở.
import { useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import type { Citation } from "../../types";
import { citationLocation, documentPageHref } from "../../utils/legalCitation";
import Icon from "../common/Icon";
import IconButton from "../common/IconButton";
import DocumentViewer from "./DocumentViewer";

interface Props {
  citation: Citation;
  onClose: () => void;
}

const FOCUSABLE = 'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])';

export default function DocumentDrawer({ citation, onClose }: Props) {
  const panel = useRef<HTMLElement>(null);
  const closeButton = useRef<HTMLButtonElement>(null);

  // Trả focus về nút citation/marker đã mở ngăn khi ngăn đóng.
  useEffect(() => {
    const opener = document.activeElement as HTMLElement | null;
    return () => opener?.focus?.();
  }, []);

  useEffect(() => {
    closeButton.current?.focus();
  }, [citation]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
        return;
      }
      if (e.key !== "Tab" || !panel.current) return;
      const items = [...panel.current.querySelectorAll<HTMLElement>(FOCUSABLE)];
      if (items.length === 0) return;
      const first = items[0];
      const last = items[items.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <>
      <div className="fixed inset-0 z-30 bg-[rgba(18,27,46,0.35)]" onClick={onClose} />
      <aside
        ref={panel}
        role="dialog"
        aria-modal="true"
        aria-label={`Nguyên văn ${citationLocation(citation)}, ${citation.document_title}`}
        data-testid="drawer"
        className="fixed inset-y-0 right-0 z-[31] flex w-[min(560px,100vw)] animate-drawer-in flex-col bg-surface shadow-[-12px_0_40px_-16px_rgba(18,27,46,0.4)]"
      >
        <div className="flex h-[58px] flex-none items-center justify-between gap-2 border-b border-line pr-3 pl-[22px] max-[600px]:pl-4">
          <span className="min-w-0 truncate font-serif text-[16px] font-semibold">
            Nguyên văn điều luật
            <span className="ml-2 font-sans text-[13px] font-medium text-muted">Căn cứ {citation.citation_id}</span>
          </span>
          <div className="flex flex-none items-center gap-1">
            <Link
              to={documentPageHref(citation)}
              data-testid="open-page"
              className="rounded-lg px-2.5 py-1.5 text-[13px] font-medium text-muted hover:bg-ink/6 hover:text-ink"
            >
              Mở trang riêng
            </Link>
            <IconButton ref={closeButton} className="inline-grid" onClick={onClose} aria-label="Đóng">
              <Icon name="close" />
            </IconButton>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-[22px] max-[600px]:p-4">
          <DocumentViewer
            documentId={citation.document_id}
            articleId={citation.article_id}
            focus={{ citationId: citation.citation_id, clause: citation.clause, point: citation.point, sourceUrl: citation.source_url }}
          />
        </div>
      </aside>
    </>
  );
}
