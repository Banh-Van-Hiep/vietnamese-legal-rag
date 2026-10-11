// Ngăn trượt bên phải để xem điều luật mà vẫn giữ nguyên hội thoại phía sau.
import { useEffect, useRef } from "react";
import type { Citation } from "../../types";
import Icon from "../common/Icon";
import IconButton from "../common/IconButton";
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
      <div className="fixed inset-0 z-30 bg-[rgba(18,27,46,0.35)]" onClick={onClose} />
      <aside
        role="dialog"
        aria-label={`Nguyên văn ${citation.article}`}
        data-testid="drawer"
        className="fixed inset-y-0 right-0 z-[31] flex w-[min(520px,100vw)] animate-drawer-in flex-col bg-surface shadow-[-12px_0_40px_-16px_rgba(18,27,46,0.4)]"
      >
        <div className="flex h-[58px] flex-none items-center justify-between border-b border-line pr-3 pl-[22px]">
          <span className="font-serif text-[16px] font-semibold">Nguyên văn điều luật</span>
          <IconButton ref={closeButton} className="inline-grid" onClick={onClose} aria-label="Đóng">
            <Icon name="close" />
          </IconButton>
        </div>
        <div className="flex-1 overflow-y-auto p-[22px]">
          <DocumentViewer documentId={citation.document_id} articleId={citation.article_id} />
        </div>
      </aside>
    </>
  );
}
