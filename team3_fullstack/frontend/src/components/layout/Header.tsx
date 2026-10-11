// Thanh tiêu đề.
import Icon from "../common/Icon";

interface Props {
  title?: string;
  onOpenSidebar: () => void;
}

export default function Header({ title, onOpenSidebar }: Props) {
  return (
    <header className="header">
      <button className="icon-btn header__menu" onClick={onOpenSidebar} aria-label="Mở thanh bên">
        <Icon name="menu" />
      </button>

      <h1 className="header__title">{title ?? "Câu hỏi mới"}</h1>

      {title && (
        <div className="header__actions">
          <button className="icon-btn" type="button" aria-label="Chia sẻ">
            <Icon name="share" />
          </button>
          <button className="icon-btn" type="button" aria-label="Thêm tùy chọn">
            <Icon name="more" />
          </button>
        </div>
      )}
    </header>
  );
}
