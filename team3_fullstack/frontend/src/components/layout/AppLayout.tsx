// Khung chung của các trang: thanh bên + vùng nội dung.
import { Outlet } from "react-router-dom";
import { AppProvider } from "../../context/AppContext";
import Sidebar from "./Sidebar";

export default function AppLayout() {
  return (
    <AppProvider>
      <div className="app">
        <Sidebar />
        <main className="main">
          <Outlet />
        </main>
      </div>
    </AppProvider>
  );
}
