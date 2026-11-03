/** Development opt-in; this is client request-to-complete time for one attempt. */
export default function DebugLatencyBadge({ elapsedMs }: { elapsedMs?: number }) {
  if (!import.meta.env.DEV || import.meta.env.VITE_DEBUG_LATENCY !== "true"
      || elapsedMs === undefined || !Number.isFinite(elapsedMs) || elapsedMs < 0) return null;
  const seconds = new Intl.NumberFormat("vi-VN", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(elapsedMs / 1000);
  return <span data-testid="latency-badge" className="mt-2 inline-block text-xs tabular-nums text-muted"
    title="Thời gian từ gửi request đến nhận complete tại trình duyệt; tính riêng từng lượt, kể cả replay.">
    Phản hồi: {seconds} s
  </span>;
}
