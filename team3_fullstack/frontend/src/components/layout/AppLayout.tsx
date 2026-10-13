// Khung chung của các trang: thanh bên + vùng nội dung.
import { Outlet } from "react-router-dom";
import { AppProvider } from "../../context/AppContext";
import Sidebar from "./Sidebar";

export default function AppLayout() {
  return (
    <AppProvider>
      <div className="flex h-full">
        <Sidebar />
        <main className="flex min-w-0 flex-1 flex-col bg-surface">
          <Outlet />
        </main>
      </div>
    </AppProvider>
  );
}
