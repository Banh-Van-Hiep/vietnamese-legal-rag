// Tải nguyên văn một điều luật theo ID, phân biệt đang tải / có dữ liệu / không tìm thấy / lỗi.
import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "../api/client";
import { getArticle } from "../api/documentApi";
import type { ArticleResponse } from "../types";

export type ArticleState =
  | { status: "loading" }
  | { status: "ready"; article: ArticleResponse }
  | { status: "not_found"; message: string }
  | { status: "error"; message: string; requestId: string | null };

export function useArticle(documentId: string, articleId: string) {
  const [state, setState] = useState<ArticleState>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);
  const key = `${documentId}/${articleId}`;
  const selected = useRef(key); selected.current = key;
  const [loadedFor, setLoadedFor] = useState(key);

  useEffect(() => {
    const controller = new AbortController();
    setState({ status: "loading" });
    setLoadedFor(key);
    getArticle(documentId, articleId, controller.signal)
      .then((article) => { if (!controller.signal.aborted && selected.current === key) setState({ status: "ready", article }); })
      .catch((error) => {
        if (controller.signal.aborted || selected.current !== key) return;
        if (error instanceof ApiError && (error.code === "DOCUMENT_NOT_FOUND" || error.code === "ARTICLE_NOT_FOUND")) {
          setState({ status: "not_found", message: error.message });
        } else if (error instanceof ApiError) {
          setState({ status: "error", message: error.message, requestId: error.requestId });
        } else {
          setState({ status: "error", message: "Không mở được điều luật. Thử lại sau.", requestId: null });
        }
      });
    return () => controller.abort();
  }, [documentId, articleId, attempt, key]);

  return { state: loadedFor === key ? state : { status: "loading" } as ArticleState, retry: useCallback(() => setAttempt((n) => n + 1), []) };
}
