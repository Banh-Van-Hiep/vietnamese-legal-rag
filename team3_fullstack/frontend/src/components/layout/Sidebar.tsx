// Danh sách hội thoại lấy từ backend, chia theo thời điểm cập nhật.
import { useMemo } from "react";
import { Link, NavLink, useMatch, useNavigate } from "react-router-dom";
import { useApp } from "../../context/AppContext";
import { groupConversations } from "../../utils/groupConversations";
import Icon from "../common/Icon";
import Seal from "../common/Seal";

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
      <div className={`sidebar-backdrop ${sidebarOpen ? "is-open" : ""}`} onClick={closeSidebar} />
      <aside className={`sidebar ${sidebarOpen ? "is-open" : ""}`} aria-label="Lịch sử hỏi đáp">
        <div className="sidebar__brand">
          <Seal size={34} />
          <div className="sidebar__brand-text">
            <span className="sidebar__name">Legal AI</span>
            <span className="sidebar__tagline">Trợ lý Luật Doanh nghiệp</span>
          </div>
          <button className="icon-btn sidebar__close" onClick={closeSidebar} aria-label="Đóng thanh bên">
            <Icon name="close" />
          </button>
        </div>

        <Link to="/" className="sidebar__new" onClick={closeSidebar}>
          <Icon name="plus" size={16} />
          Câu hỏi mới
        </Link>

        <nav className="sidebar__history" aria-label="Hội thoại">
          {app.listStatus === "loading" && <p className="sidebar__note">Đang tải lịch sử…</p>}
          {app.listStatus === "error" && (
            <p className="sidebar__note">
              {app.listError}{" "}
              <button className="sidebar__retry" type="button" onClick={app.refresh}>Thử lại</button>
            </p>
          )}
          {app.listStatus === "ready" && groups.length === 0 && (
            <p className="sidebar__note">Chưa có hội thoại nào. Đặt câu hỏi đầu tiên để bắt đầu.</p>
          )}
          {groups.map((group) => (
            <section key={group.label} className="history-group">
              <h2 className="history-group__label">{group.label}</h2>
              <ul>
                {group.items.map((c) => (
                  <li key={c.conversation_id} className="history-row">
                    <NavLink
                      to={`/c/${c.conversation_id}`}
                      className={({ isActive }) => `history-item ${isActive ? "is-active" : ""}`}
                      onClick={closeSidebar}
                    >
                      <span className="history-item__title">{c.title}</span>
                    </NavLink>
                    <button
                      className="history-row__delete"
                      type="button"
                      aria-label={`Xóa hội thoại ${c.title}`}
                      onClick={() => handleDelete(c.conversation_id, c.title)}
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
          <p className="sidebar__alert" role="alert">
            {app.actionError}{" "}
            <button className="sidebar__retry" type="button" onClick={app.dismissActionError}>Đóng</button>
          </p>
        )}

        <div className="sidebar__footer">
          <NavLink
            to="/search"
            className={({ isActive }) => `sidebar__link ${isActive ? "is-active" : ""}`}
            onClick={closeSidebar}
          >
            <Icon name="book" size={17} />
            Tra cứu văn bản luật
          </NavLink>
          <div className="sidebar__user">
            <span className="avatar">K</span>
            <span className="sidebar__user-name">Khách</span>
          </div>
        </div>
      </aside>
    </>
  );
}
