// API xem nguyên văn điều luật. ID lấy từ Citation, không suy ra từ tên hiển thị.
import { request } from "./client";
import type { ArticleResponse } from "../types";

export const getArticle = (documentId: string, articleId: string, signal?: AbortSignal) =>
  request<ArticleResponse>(
    `/api/v1/documents/${encodeURIComponent(documentId)}/articles/${encodeURIComponent(articleId)}`,
    { signal, timeoutMs: 15_000 },
  );
