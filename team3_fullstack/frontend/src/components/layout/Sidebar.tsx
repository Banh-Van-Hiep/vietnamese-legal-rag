// Danh sách hội thoại lấy từ backend, chia theo thời điểm cập nhật.
import { useMemo } from "react";
import { Link, NavLink, useMatch, useNavigate } from "react-router-dom";
import { useApp } from "../../context/AppContext";
import { groupConversations } from "../../utils/groupConversations";
import Icon from "../common/Icon";
import IconButton from "../common/IconButton";
import Seal from "../common/Seal";

// Hàng ở thanh bên (hội thoại, liên kết tra cứu): nền sáng nhẹ khi rê chuột, sáng hơn khi đang mở.
const rowBase = "block rounded-lg text-[14px] hover:bg-white/6";
const rowActive = "bg-white/11 text-white";

export default function Sidebar() {
  const app = useApp();
  const navigate = useNavigate();
  const current = useMatch("/c/:conversationId")?.params.conversationId;
  const groups = useMemo(() => groupConversations(app.conversations), [app.conversations]);
  const { sidebarOpen, closeSidebar } = app;

  async function handleDelete(id: string, title: string) {
    if (!window.confirm(`Xóa hội thoại "${title}"? Toàn bộ tin nhắn trong hội thoại sẽ mất.`)) return;
    const removed = await app.remove(id);
    if (removed && id === current) navigate("/");
  }

  return (
    <>
      <div
        onClick={closeSidebar}
        data-testid="sidebar-backdrop"
        className={`pointer-events-none fixed inset-0 z-10 hidden bg-[rgba(18,27,46,0.45)] opacity-0 transition-opacity duration-[220ms] ease-in-out max-[860px]:block ${
          sidebarOpen ? "max-[860px]:pointer-events-auto max-[860px]:opacity-100" : ""
        }`}
      />
      <aside
        aria-label="Lịch sử hỏi đáp"
        data-testid="sidebar"
        data-open={sidebarOpen}
        className={`flex w-[280px] flex-none flex-col gap-3 bg-ink-900 px-3 pt-4 pb-3 text-side-text max-[860px]:fixed max-[860px]:inset-y-0 max-[860px]:left-0 max-[860px]:z-20 max-[860px]:w-[min(86vw,280px)] max-[860px]:transition-transform max-[860px]:duration-[220ms] max-[860px]:ease-in-out ${
          sidebarOpen ? "max-[860px]:translate-x-0" : "max-[860px]:-translate-x-full"
        }`}
      >
        <div className="flex items-center gap-3 px-1.5 pt-1 pb-2">
          <Seal size={34} tone="dark" />
          <div className="flex min-w-0 flex-col leading-[1.25]">
            <span className="font-serif text-[18px] font-bold text-white">Legal AI</span>
            <span className="text-[12.5px] text-side-muted">Trợ lý Luật Doanh nghiệp</span>
          </div>
          <IconButton
            tone="dark"
            className="ml-auto hidden max-[860px]:inline-grid"
            onClick={closeSidebar}
            aria-label="Đóng thanh bên"
            data-testid="close-sidebar"
          >
            <Icon name="close" />
          </IconButton>
        </div>

        <Link
          to="/"
          onClick={closeSidebar}
          data-testid="new-chat"
          className="flex items-center gap-2 rounded-[10px] bg-surface px-3.5 py-2.5 text-[14px] font-semibold text-ink-900 hover:bg-[#eef1f6]"
        >
          <Icon name="plus" size={16} />
          Câu hỏi mới
        </Link>

        <nav
          aria-label="Hội thoại"
          className="-mx-1 flex-1 overflow-y-auto p-1 [scrollbar-color:rgba(255,255,255,0.15)_transparent] [scrollbar-width:thin]"
        >
          {app.listStatus === "loading" && <p className="mx-1 my-1.5 px-1.5 text-[13.5px] text-side-muted">Đang tải lịch sử…</p>}
          {app.listStatus === "error" && (
            <p className="mx-1 my-1.5 px-1.5 text-[13.5px] text-side-muted">
              {app.listError}{" "}
              <button className="text-white underline underline-offset-[3px]" type="button" onClick={app.refresh}>
                Thử lại
              </button>
            </p>
          )}
          {app.listStatus === "ready" && groups.length === 0 && (
            <p className="mx-1 my-1.5 px-1.5 text-[13.5px] text-side-muted">
              Chưa có hội thoại nào. Đặt câu hỏi đầu tiên để bắt đầu.
            </p>
          )}
          {groups.map((group, index) => (
            <section key={group.label} className={index > 0 ? "mt-[18px]" : ""}>
              <h2 className="mb-1 px-2.5 text-[12.5px] font-medium text-side-muted">{group.label}</h2>
              <ul>
                {group.items.map((c) => (
                  <li key={c.conversation_id} className="group relative" data-testid="history-row">
                    <NavLink
                      to={`/c/${c.conversation_id}`}
                      onClick={closeSidebar}
                      data-testid="history-item"
                      className={({ isActive }) =>
                        `${rowBase} relative py-[7px] pr-9 pl-2.5 ${
                          isActive
                            ? `${rowActive} before:absolute before:inset-y-[9px] before:left-0 before:w-[3px] before:rounded-xs before:bg-seal-light before:content-['']`
                            : ""
                        }`
                      }
                    >
                      <span className="block truncate">{c.title}</span>
                    </NavLink>
                    <button
                      type="button"
                      data-testid="delete-conversation"
                      aria-label={`Xóa hội thoại ${c.title}`}
                      onClick={() => handleDelete(c.conversation_id, c.title)}
                      className="absolute top-1/2 right-1 grid size-7 -translate-y-1/2 place-items-center rounded-md text-side-muted opacity-0 group-focus-within:opacity-100 group-hover:opacity-100 hover:bg-white/6 hover:text-white [@media(hover:none)]:opacity-100"
                    >
                      <Icon name="trash" size={15} />
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </nav>

        {app.actionError && (
          <p role="alert" className="mx-1 my-1.5 rounded-lg bg-[rgba(226,85,75,0.14)] px-2.5 py-2 text-[13.5px] text-[#f4b8b3]">
            {app.actionError}{" "}
            <button className="text-white underline underline-offset-[3px]" type="button" onClick={app.dismissActionError}>
              Đóng
            </button>
          </p>
        )}

        <div className="flex flex-col gap-1 border-t border-white/8 pt-2.5">
          <NavLink
            to="/search"
            onClick={closeSidebar}
            data-testid="nav-search"
            className={({ isActive }) => `${rowBase} flex items-center gap-2.5 px-2.5 py-2 text-left ${isActive ? rowActive : ""}`}
          >
            <Icon name="book" size={17} />
            Tra cứu văn bản luật
          </NavLink>
          <div className="flex items-center gap-2.5 pt-1.5 pr-1 pb-0.5 pl-2.5 text-[14px]">
            <span className="inline-grid size-[30px] place-items-center rounded-full bg-ink-700 text-[13px] font-semibold text-white">K</span>
            <span>Khách</span>
          </div>
        </div>
      </aside>
    </>
  );
}
