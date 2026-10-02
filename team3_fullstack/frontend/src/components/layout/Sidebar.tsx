// Danh sách hội thoại.
import { Link, NavLink } from "react-router-dom";
import Icon from "../common/Icon";
import Seal from "../common/Seal";
import { mockConversationGroups } from "../../mocks/chatMock";

interface Props {
  open: boolean;
  onClose: () => void;
}

export default function Sidebar({ open, onClose }: Props) {
  return (
    <>
      <div className={`sidebar-backdrop ${open ? "is-open" : ""}`} onClick={onClose} />
      <aside className={`sidebar ${open ? "is-open" : ""}`} aria-label="Lịch sử hỏi đáp">
        <div className="sidebar__brand">
          <Seal size={34} />
          <div className="sidebar__brand-text">
            <span className="sidebar__name">Legal AI</span>
            <span className="sidebar__tagline">Trợ lý luật lao động Việt Nam</span>
          </div>
          <button className="icon-btn sidebar__close" onClick={onClose} aria-label="Đóng thanh bên">
            <Icon name="close" />
          </button>
        </div>

        <Link to="/" className="sidebar__new" onClick={onClose}>
          <Icon name="plus" size={16} />
          Câu hỏi mới
        </Link>

        <label className="sidebar__search">
          <Icon name="search" size={16} />
          <input type="search" placeholder="Tìm trong lịch sử" />
        </label>

        <nav className="sidebar__history">
          {mockConversationGroups.map((group) => (
            <section key={group.label} className="history-group">
              <h2 className="history-group__label">{group.label}</h2>
              <ul>
                {group.items.map((c) => (
                  <li key={c.id}>
                    <NavLink
                      to={`/c/${c.id}`}
                      className={({ isActive }) => `history-item ${isActive ? "is-active" : ""}`}
                      onClick={onClose}
                    >
                      <span className="history-item__title">{c.title}</span>
                    </NavLink>
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </nav>

        <div className="sidebar__footer">
          <button className="sidebar__link" type="button">
            <Icon name="book" size={17} />
            Tra cứu văn bản luật lao động
          </button>
          <div className="sidebar__user">
            <span className="avatar">K</span>
            <span className="sidebar__user-name">Khách</span>
            <button className="icon-btn" type="button" aria-label="Tùy chọn tài khoản">
              <Icon name="more" />
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}
