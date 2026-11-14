import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import type { UiMessage } from "../types";
import ChatPage from "./ChatPage";

const mocks = vi.hoisted(() => ({
  conversationId: "101" as string | undefined,
  messages: [] as UiMessage[],
  receiving: false,
  reload: vi.fn(),
}));

vi.mock("react-router-dom", async (importOriginal) => ({
  ...await importOriginal<typeof import("react-router-dom")>(),
  useParams: () => ({ conversationId: mocks.conversationId }),
  useNavigate: () => vi.fn(),
}));
vi.mock("../context/AppContext", () => ({
  useApp: () => ({ conversations: [], refresh: vi.fn(), openSidebar: vi.fn() }),
}));
vi.mock("../hooks/useChat", () => ({
  MAX_QUESTION_LENGTH: 2000,
  useChat: () => ({
    messages: mocks.messages, loading: false, loadError: null, receiving: mocks.receiving,
    sending: true, send: vi.fn(), retry: vi.fn(), reload: mocks.reload, stopReceiving: vi.fn(),
  }),
}));

const unresolved: UiMessage = {
  key: "a-stopped", clientRequestId: "44444444-4444-4444-8444-444444444444",
  role: "assistant", state: "failed", content: null, answerStatus: null, citations: [],
  failure: { code: "RECEIVING_STOPPED", message: "Đã dừng nhận.", requestId: null,
    retryable: true, outcomeUnknown: true },
};

beforeEach(() => {
  mocks.conversationId = "101";
  mocks.messages = [unresolved];
  mocks.receiving = false;
  vi.clearAllMocks();
});

describe("ChatPage recovery actions", () => {
  it("offers state refresh after Stop once the conversation is known", () => {
    const html = renderToStaticMarkup(<ChatPage />);
    expect(html).toContain("Tải lại trạng thái");
    expect(html).toContain("Chưa xác định được kết quả lượt hỏi trên máy chủ.");
    expect(html).toContain("Thử lại");
    expect(mocks.reload).not.toHaveBeenCalled();
  });

  it("keeps pending-history refresh and blocks sending", () => {
    mocks.messages = [{ ...unresolved, state: "pending", failure: undefined }];
    const html = renderToStaticMarkup(<ChatPage />);
    expect(html).toContain("Lượt hỏi đang được xử lý trên máy chủ.");
    expect(html).toContain("Tải lại trạng thái");
    expect(html).toMatch(/data-testid="send"[^>]*disabled/);
  });

  it("retains safe retry before meta without offering history for an unknown conversation", () => {
    mocks.conversationId = undefined;
    const html = renderToStaticMarkup(<ChatPage />);
    expect(html).toContain("Thử lại");
    expect(html).not.toContain("Tải lại trạng thái");
  });

  it("offers Stop while receiving without concurrent history refresh", () => {
    mocks.receiving = true;
    mocks.messages = [{ ...unresolved, state: "pending", failure: undefined }];
    const html = renderToStaticMarkup(<ChatPage />);
    expect(html).toContain("Dừng nhận");
    expect(html).not.toContain("Tải lại trạng thái");
  });
});
