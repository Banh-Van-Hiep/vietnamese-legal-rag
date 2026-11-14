import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import MessageBubble from "./MessageBubble";
import type { Citation, UiMessage } from "../../types";

// VLRA-70: phân biệt câu trả lời có căn cứ, thiếu căn cứ (không phải lỗi) và lỗi hệ thống.
const citation: Citation = {
  citation_id: "C1", chunk_id: "luat-59-2020-qh14-v1__dieu-74__k1__0", document_id: "luat-59-2020-qh14-v1",
  article_id: "dieu-74", document_title: "Luật Doanh nghiệp", article: "Điều 74", clause: "Khoản 1", point: null,
  source_url: "https://vbpl.vn/van-ban/chi-tiet/142881",
};
const base: UiMessage = { key: "a-1", role: "assistant", state: "completed", content: "Công ty TNHH một thành viên [C1].",
  answerStatus: "answered", citations: [citation] };
const render = (m: UiMessage, isLast = true) =>
  renderToStaticMarkup(<MessageBubble message={m} isLast={isLast} onRetry={() => {}} onOpenCitation={() => {}} />);
const count = (html: string, testId: string) => html.split(`data-testid="${testId}"`).length - 1;

describe("MessageBubble", () => {
  it("answered: hiển thị câu trả lời và đúng một thẻ citation có nút mở nguyên văn", () => {
    const html = render(base);
    expect(count(html, "citation")).toBe(1);
    expect(count(html, "open-article")).toBe(1);
    expect(html).toContain("Điều 74");
    expect(html).not.toContain('data-testid="notice-error"');
    expect(html).not.toContain('data-testid="notice-info"');
  });
  it("insufficient_context: thông báo thiếu căn cứ, không có citation và không hiển thị như lỗi", () => {
    const html = render({ ...base, answerStatus: "insufficient_context", content: "Chưa đủ căn cứ trong dữ liệu.", citations: [] });
    expect(html).toContain('data-testid="notice-info"');
    expect(html).toContain("Chưa đủ căn cứ trong dữ liệu.");
    expect(count(html, "citation")).toBe(0);
    expect(html).not.toContain('data-testid="notice-error"');
    expect(html).not.toContain('role="alert"');
  });
  it("lỗi retryable ở lượt cuối mới có nút Thử lại; lỗi không retryable thì không", () => {
    const failed = (retryable: boolean): UiMessage => ({ ...base, state: "failed", content: null, answerStatus: null, citations: [],
      failure: { code: retryable ? "SERVICE_UNAVAILABLE" : "UPSTREAM_INVALID_RESPONSE", message: "Câu an toàn.", requestId: "trace-1", retryable } });
    expect(render(failed(true))).toContain("Thử lại");
    expect(render(failed(true), false)).not.toContain("Thử lại");
    const html = render(failed(false));
    expect(html).toContain('data-testid="notice-error"');
    expect(html).toContain("Câu an toàn.");
    expect(html).not.toContain("Thử lại");
    expect(count(html, "citation")).toBe(0);
  });
});
