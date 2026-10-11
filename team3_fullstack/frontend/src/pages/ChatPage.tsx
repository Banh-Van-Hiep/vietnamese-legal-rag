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
                ? "Hội thoại này đã bị xóa hoặc không còn trên máy chủ (dữ liệu thử nghiệm sẽ mất khi backend khởi động lại)."
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
            onOpenCitation={setOpenCitation}
          />
          <ChatInput onSend={chat.send} sending={chat.sending} />
        </>
      )}
      {openCitation && <DocumentDrawer citation={openCitation} onClose={closeCitation} />}
    </>
  );
}
