// Trang tra cứu (khung): nhập từ khóa, tìm trong dữ liệu mẫu, mở nguyên văn điều luật theo ID.
import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { cardClass, openLinkClass } from "../components/common/classes";
import Icon from "../components/common/Icon";
import MockBadge from "../components/common/MockBadge";
import Notice from "../components/common/Notice";
import Header from "../components/layout/Header";
import { searchFixtures, type SearchFixture } from "../data/searchFixtures";
import { normalize } from "../utils/text";

type Outcome = { keyword: string; results: SearchFixture[] };

function search(keyword: string): SearchFixture[] {
  const needle = normalize(keyword);
  return searchFixtures.filter((f) =>
    normalize(`${f.document_title} ${f.article} ${f.excerpt}`).includes(needle),
  );
}

export default function SearchPage() {
  const [value, setValue] = useState("");
  const [hint, setHint] = useState("");
  const [outcome, setOutcome] = useState<Outcome | null>(null);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const keyword = value.trim();
    if (!keyword) {
      setHint("Nhập từ khóa để tìm.");
      setOutcome(null);
      return;
    }
    setHint("");
    setOutcome({ keyword, results: search(keyword) });
  }

  return (
    <>
      <Header title="Tra cứu văn bản luật" />
      <div className="flex-1 overflow-y-auto px-6 max-[600px]:px-4">
        <div className="mx-auto max-w-[760px] pt-7 pb-10">
          <form
            onSubmit={handleSubmit}
            role="search"
            className="flex items-center gap-2.5 rounded-xl border border-line-strong bg-surface py-1.5 pr-1.5 pl-4 text-muted focus-within:border-ink-700"
          >
            <Icon name="search" size={18} />
            <input
              type="search"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder="Nhập từ khóa, ví dụ: kiểm thử"
              aria-label="Từ khóa tra cứu"
              data-testid="search-input"
              className="h-[38px] min-w-0 flex-1 border-0 bg-transparent px-0.5 py-px text-[15.5px] text-ink outline-0"
            />
            <button
              type="submit"
              data-testid="search-submit"
              className="h-[38px] rounded-lg bg-ink-900 px-5 font-medium text-white hover:bg-ink-700"
            >
              Tìm
            </button>
          </form>
          {hint && (
            <p role="alert" data-testid="search-hint" className="mx-1 mt-2 text-[13.5px] text-seal-strong">
              {hint}
            </p>
          )}

          <p data-testid="search-note" className="mt-3.5 mb-[22px] flex flex-wrap items-center gap-2.5 text-[13.5px] text-muted">
            <MockBadge />
            Chưa có tìm kiếm thật. Kết quả bên dưới lấy từ vài mục mẫu để thử luồng mở điều luật.
          </p>

          {!outcome && !hint && (
            <p className="mt-6 text-center text-muted">Nhập từ khóa rồi bấm Tìm để xem kết quả.</p>
          )}

          {outcome && outcome.results.length === 0 && (
            <Notice variant="info" role="status" testId="notice-info" title="Không có kết quả">
              <p>Không có mục mẫu nào khớp với “{outcome.keyword}”. Thử từ khóa khác.</p>
            </Notice>
          )}

          {outcome && outcome.results.length > 0 && (
            <>
              <p className="mb-2.5 text-[14px] text-muted" role="status">
                {outcome.results.length} kết quả cho “{outcome.keyword}”
              </p>
              <ul className="flex flex-col gap-2.5">
                {outcome.results.map((r) => (
                  <li key={`${r.document_id}/${r.article_id}`} className={cardClass} data-testid="search-result">
                    <h3 className="font-serif text-[16px] font-bold text-ink-950">{r.article}</h3>
                    <p className="mt-0.5 text-[13px] text-muted">{r.document_title}</p>
                    <p className="mt-2.5 font-serif text-[14.5px] leading-[1.75]">{r.excerpt}</p>
                    {r.note && <p className="mt-1.5 text-[13px] text-mock-ink">{r.note}</p>}
                    <Link
                      className={`${openLinkClass} mt-2`}
                      to={`/documents/${encodeURIComponent(r.document_id)}/articles/${encodeURIComponent(r.article_id)}`}
                    >
                      Xem nguyên văn điều luật
                    </Link>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      </div>
    </>
  );
}
