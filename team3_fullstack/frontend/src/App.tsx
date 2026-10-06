// Định tuyến các trang.
import { Route, Routes } from "react-router-dom";
import ChatPage from "./pages/ChatPage";
import DocumentPage from "./pages/DocumentPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<ChatPage />} />
      <Route path="/c/:conversationId" element={<ChatPage />} />
      <Route path="/documents/:docId" element={<DocumentPage />} />
    </Routes>
  );
}
