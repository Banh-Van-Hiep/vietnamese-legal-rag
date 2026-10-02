// Trang hỏi đáp: Sidebar + ChatWindow. Hiện dùng dữ liệu mẫu, chưa gọi backend.
import { useState } from "react";
import { useParams } from "react-router-dom";
import Sidebar from "../components/layout/Sidebar";
import Header from "../components/layout/Header";
import ChatWindow from "../components/chat/ChatWindow";
import ChatInput from "../components/chat/ChatInput";
import { findConversationTitle, mockMessages } from "../mocks/chatMock";

export default function ChatPage() {
  const { conversationId } = useParams();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const title = conversationId ? findConversationTitle(Number(conversationId)) : undefined;
  const messages = conversationId ? mockMessages : [];

  return (
    <div className="app">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <main className="main">
        <Header title={title} onOpenSidebar={() => setSidebarOpen(true)} />
        <ChatWindow messages={messages} />
        <ChatInput />
      </main>
    </div>
  );
}
