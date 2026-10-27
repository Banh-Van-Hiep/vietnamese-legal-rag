// Trang hỏi đáp: gửi câu hỏi tới backend, hiển thị câu trả lời và mở nguyên văn điều luật được trích dẫn.
import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import ChatInput from "../components/chat/ChatInput";
import ChatWindow from "../components/chat/ChatWindow";
import Notice, { noticeActionClass } from "../components/common/Notice";
import DocumentDrawer from "../components/document/DocumentDrawer";
import Header from "../components/layout/Header";
import { useApp } from "../context/AppContext";
import { useChat } from "../hooks/useChat";
import type { Citation } from "../types";

export default function ChatPage() {
  const { conversationId } = useParams();
  const navigate = useNavigate();
  const { conversations, refresh } = useApp();
  const [openCitation, setOpenCitation] = useState<{ messageKey: string; citation: Citation } | null>(null);

  const chat = useChat({
    conversationId,
    onConversationCreated: (id) => navigate(`/c/${id}`, { replace: true }),
    onChanged: refresh,
  });

  // Đổi hội thoại thì đóng ngăn xem điều luật của hội thoại trước.
  useEffect(() => setOpenCitation(null), [conversationId]);
  const closeCitation = useCallback(() => setOpenCitation(null), []);
  const openSource = useCallback((messageKey: string, citation: Citation) => setOpenCitation({ messageKey, citation }), []);

  const title = conversationId
    ? conversations.find((c) => c.conversation_id === conversationId)?.title ?? "Hội thoại"
    : undefined;

  return (
    <>
      <Header title={title} />
      {chat.loadError ? (
        <div className="flex-1 overflow-y-auto px-6 max-[600px]:px-4">
          <Notice
            variant="error"
            role="alert"
            testId="notice-page"
            className="mx-auto mt-[12vh] max-w-[560px]"
            title={chat.loadError.notFound ? "Không tìm thấy hội thoại" : "Chưa tải được hội thoại"}
            action={
              chat.loadError.notFound ? (
                <Link className={noticeActionClass} to="/">Bắt đầu hội thoại mới</Link>
              ) : (
                <button className={noticeActionClass} type="button" onClick={chat.reload}>Thử lại</button>
              )
            }
          >
            <p>
              {chat.loadError.notFound
                ? "Hội thoại này đã bị xóa hoặc không còn trên máy chủ."
                : chat.loadError.message}
            </p>
          </Notice>
        </div>
      ) : (
        <>
          <ChatWindow
            messages={chat.messages}
            loading={chat.loading}
            onSuggestion={chat.send}
            onRetry={chat.retry}
            openCitation={openCitation && { messageKey: openCitation.messageKey, citationId: openCitation.citation.citation_id }}
            onOpenCitation={openSource}
          />
          {chat.receiving && (
            <div className="flex justify-center py-2">
              <button className={noticeActionClass} type="button" onClick={chat.stopReceiving}>Dừng nhận</button>
            </div>
          )}
          {chat.sending && !chat.receiving && chat.messages.some((m) => m.state === "pending") && (
            <div className="px-6 py-2 text-center text-[13.5px] text-muted" role="status">
              Lượt hỏi đang được xử lý trên máy chủ.{" "}
              <button className={noticeActionClass} type="button" onClick={chat.reload}>Tải lại trạng thái</button>
            </div>
          )}
          <ChatInput onSend={chat.send} sending={chat.sending} />
        </>
      )}
      {openCitation && <DocumentDrawer citation={openCitation.citation} onClose={closeCitation} />}
    </>
  );
}
