import { v2Article } from "./publicApi";
export async function getArticle(documentId: string, articleId: string, signal?: AbortSignal) {
  return v2Article(documentId, articleId, signal);
}
