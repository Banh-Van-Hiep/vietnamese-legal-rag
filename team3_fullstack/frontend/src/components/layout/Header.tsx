// Thanh tiêu đề.
import { useApp } from "../../context/AppContext";
import Icon from "../common/Icon";
import MockBadge from "../common/MockBadge";

interface Props {
  title?: string;
}

export default function Header({ title }: Props) {
  const { openSidebar } = useApp();
  return (
    <header className="header">
      <button className="icon-btn header__menu" onClick={openSidebar} aria-label="Mở thanh bên">
        <Icon name="menu" />
      </button>
      <h1 className="header__title">{title ?? "Câu hỏi mới"}</h1>
      <MockBadge />
    </header>
  );
}
