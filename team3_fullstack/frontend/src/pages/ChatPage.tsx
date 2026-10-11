// Trang hỏi đáp: gửi câu hỏi tới backend, hiển thị câu trả lời và mở nguyên văn điều luật được trích dẫn.
import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import ChatInput from "../components/chat/ChatInput";
import ChatWindow from "../components/chat/ChatWindow";
import Icon from "../components/common/Icon";
import DocumentDrawer from "../components/document/DocumentDrawer";
import Header from "../components/layout/Header";
import { useApp } from "../context/AppContext";
import { useChat } from "../hooks/useChat";
import type { Citation } from "../types";

export default function ChatPage() {
  const { conversationId } = useParams();
  const navigate = useNavigate();
  const { conversations, refresh } = useApp();
  const [openCitation, setOpenCitation] = useState<Citation | null>(null);

  const chat = useChat({
    conversationId,
    onConversationCreated: (id) => navigate(`/c/${id}`, { replace: true }),
    onChanged: refresh,
  });

  // Đổi hội thoại thì đóng ngăn xem điều luật của hội thoại trước.
  useEffect(() => setOpenCitation(null), [conversationId]);
  const closeCitation = useCallback(() => setOpenCitation(null), []);

  const title = conversationId
    ? conversations.find((c) => c.conversation_id === conversationId)?.title ?? "Hội thoại"
    : undefined;

  return (
    <>
      <Header title={title} />
      {chat.loadError ? (
        <div className="chat-scroll">
          <div className="notice notice--error notice--page" role="alert">
            <Icon name="alert" size={18} />
            <div>
              <p className="notice__title">
                {chat.loadError.notFound ? "Không tìm thấy hội thoại" : "Chưa tải được hội thoại"}
              </p>
              <p>
                {chat.loadError.notFound
                  ? "Hội thoại này đã bị xóa hoặc không còn trên máy chủ (dữ liệu thử nghiệm sẽ mất khi backend khởi động lại)."
                  : chat.loadError.message}
              </p>
              {chat.loadError.notFound ? (
                <Link className="notice__action" to="/">Bắt đầu hội thoại mới</Link>
              ) : (
                <button className="notice__action" type="button" onClick={chat.reload}>Thử lại</button>
              )}
            </div>
          </div>
        </div>
      ) : (
        <>
          <ChatWindow
            messages={chat.messages}
            loading={chat.loading}
            onSuggestion={chat.send}
            onRetry={chat.retry}
            onOpenCitation={setOpenCitation}
          />
          <ChatInput onSend={chat.send} sending={chat.sending} />
        </>
      )}
      {openCitation && <DocumentDrawer citation={openCitation} onClose={closeCitation} />}
    </>
  );
}
