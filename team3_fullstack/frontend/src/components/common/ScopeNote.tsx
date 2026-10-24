// Thông tin phạm vi dữ liệu (Docs v2.0 §8.6 "Scope information"): phạm vi corpus, bản dữ liệu và
// chế độ mock/live. Chỉ hiển thị đúng cấu hình bản phát hành, không tuyên bố đã có mọi văn bản pháp luật.
import Icon from "./Icon";
import { isMockMode } from "./MockBadge";

export const corpusScope: string =
  import.meta.env.VITE_CORPUS_SCOPE?.trim() || "Pháp luật doanh nghiệp: Luật Doanh nghiệp và các văn bản hướng dẫn trong bộ dữ liệu của dự án";
export const corpusSnapshot: string | null = import.meta.env.VITE_CORPUS_SNAPSHOT?.trim() || null;

export default function ScopeNote({ className = "" }: { className?: string }) {
  return (
    <section
      aria-label="Phạm vi dữ liệu"
      data-testid="scope-note"
      className={`rounded-sm border border-line bg-paper px-4 py-3 text-left text-[13px] leading-[1.6] text-muted ${className}`}
    >
      <p className="mb-1 flex items-center gap-1.5 font-semibold text-ink-700">
        <Icon name="book" size={15} />
        Phạm vi dữ liệu
      </p>
      <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5">
        <dt>Lĩnh vực</dt>
        <dd className="text-ink">{corpusScope}</dd>
        <dt>Bản dữ liệu</dt>
        <dd className="text-ink" data-testid="scope-snapshot">{corpusSnapshot ?? "Chưa công bố"}</dd>
        <dt>Chế độ</dt>
        <dd className="text-ink" data-testid="scope-mode">
          {isMockMode ? "Thử nghiệm: câu trả lời và nguyên văn là dữ liệu mẫu" : "Dữ liệu thật của bản phát hành"}
        </dd>
      </dl>
      <p className="mt-1.5">
        Hệ thống chỉ trả lời trong phạm vi trên và theo bản dữ liệu đã công bố, chưa bao gồm mọi văn bản pháp luật.
        Luôn đối chiếu nguyên văn và nguồn chính thức trước khi áp dụng.
      </p>
    </section>
  );
}
