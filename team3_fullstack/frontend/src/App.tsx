// Định tuyến các trang.
import { Route, Routes } from "react-router-dom";
import AppLayout from "./components/layout/AppLayout";
import BackendPlayground from "./pages/BackendPlayground";
import ChatPage from "./pages/ChatPage";
import DocumentPage from "./pages/DocumentPage";
import SearchPage from "./pages/SearchPage";

export default function App() {
  return (
    <Routes>
      <Route path="/try-backend" element={<BackendPlayground />} />
      <Route element={<AppLayout />}>
        <Route path="/" element={<ChatPage />} />
        <Route path="/c/:conversationId" element={<ChatPage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/documents/:documentId/articles/:articleId" element={<DocumentPage />} />
      </Route>
    </Routes>
  );
}
