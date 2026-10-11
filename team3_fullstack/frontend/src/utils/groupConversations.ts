import type { Conversation } from "../types";

export interface ConversationGroup {
  label: string;
  items: Conversation[];
}

const DAY = 24 * 60 * 60 * 1000;

/** Chia hội thoại theo lần cập nhật gần nhất. Giữ thứ tự backend trả về (mới nhất trước). */
export function groupConversations(list: Conversation[], now = new Date()): ConversationGroup[] {
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const groups: ConversationGroup[] = [
    { label: "Hôm nay", items: [] },
    { label: "7 ngày qua", items: [] },
    { label: "Cũ hơn", items: [] },
  ];
  for (const c of list) {
    const t = new Date(c.updated_at).getTime();
    if (t >= startOfToday) groups[0].items.push(c);
    else if (t >= startOfToday - 6 * DAY) groups[1].items.push(c);
    else groups[2].items.push(c);
  }
  return groups.filter((g) => g.items.length > 0);
}
