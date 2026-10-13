// Thanh tiêu đề.
import { useApp } from "../../context/AppContext";
import Icon from "../common/Icon";
import IconButton from "../common/IconButton";
import MockBadge from "../common/MockBadge";

interface Props {
  title?: string;
}

export default function Header({ title }: Props) {
  const { openSidebar } = useApp();
  return (
    <header className="flex h-[58px] flex-none items-center gap-2 border-b border-line pr-4 pl-6 max-[860px]:px-2">
      <IconButton className="hidden max-[860px]:inline-grid" onClick={openSidebar} aria-label="Mở thanh bên" data-testid="open-sidebar">
        <Icon name="menu" />
      </IconButton>
      <h1 className="m-0 min-w-0 flex-1 truncate font-serif text-[17px] font-semibold">{title ?? "Câu hỏi mới"}</h1>
      <MockBadge />
    </header>
  );
}
