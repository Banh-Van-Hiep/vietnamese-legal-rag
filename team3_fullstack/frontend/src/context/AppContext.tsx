// Trạng thái dùng chung cho mọi trang: danh sách hội thoại ở thanh bên và việc đóng/mở thanh bên.
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { ApiError } from "../api/client";
import { deleteConversation, listConversations } from "../api/conversationApi";
import type { Conversation } from "../types";

interface AppState {
  conversations: Conversation[];
  listStatus: "loading" | "ready" | "error";
  listError: string | null;
  refresh: () => void;
  /** Trả về true nếu đã xóa (hoặc hội thoại vốn không còn). */
  remove: (id: string) => Promise<boolean>;
  actionError: string | null;
  dismissActionError: () => void;
  sidebarOpen: boolean;
  openSidebar: () => void;
  closeSidebar: () => void;
}

const AppContext = createContext<AppState | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [listStatus, setListStatus] = useState<AppState["listStatus"]>("loading");
  const [listError, setListError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [version, setVersion] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    listConversations(controller.signal)
      .then((page) => {
        setConversations(page.items);
        setListStatus("ready");
        setListError(null);
      })
      .catch((error) => {
        if (controller.signal.aborted) return;
        setListStatus("error");
        setListError(error instanceof ApiError ? error.message : "Không tải được lịch sử hỏi đáp.");
      });
    return () => controller.abort();
  }, [version]);

  const refresh = useCallback(() => setVersion((v) => v + 1), []);

  const remove = useCallback(async (id: string) => {
    try {
      await deleteConversation(id);
    } catch (error) {
      if (error instanceof ApiError && error.code === "CONVERSATION_NOT_FOUND") {
        refresh();
        return true;
      }
      setActionError(
        error instanceof ApiError && error.code === "CONVERSATION_BUSY"
          ? "Hội thoại đang xử lý một câu hỏi. Hãy đợi câu trả lời rồi xóa lại."
          : error instanceof ApiError
            ? error.message
            : "Không xóa được hội thoại. Thử lại sau.",
      );
      return false;
    }
    setConversations((list) => list.filter((c) => c.conversation_id !== id));
    refresh();
    return true;
  }, [refresh]);

  const value = useMemo<AppState>(() => ({
    conversations, listStatus, listError, refresh, remove, actionError,
    dismissActionError: () => setActionError(null),
    sidebarOpen,
    openSidebar: () => setSidebarOpen(true),
    closeSidebar: () => setSidebarOpen(false),
  }), [conversations, listStatus, listError, refresh, remove, actionError, sidebarOpen]);

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp(): AppState {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp phải nằm trong AppProvider");
  return ctx;
}
