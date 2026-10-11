// Trang tra cứu (khung): nhập từ khóa, tìm trong dữ liệu mẫu, mở nguyên văn điều luật theo ID.
import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import Icon from "../components/common/Icon";
import MockBadge from "../components/common/MockBadge";
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
      <div className="chat-scroll">
        <div className="page">
          <form className="searchbar" onSubmit={handleSubmit} role="search">
            <Icon name="search" size={18} />
            <input
              type="search"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder="Nhập từ khóa, ví dụ: kiểm thử"
              aria-label="Từ khóa tra cứu"
            />
            <button className="searchbar__submit" type="submit">Tìm</button>
          </form>
          {hint && <p className="form-hint" role="alert">{hint}</p>}

          <p className="search-note">
            <MockBadge />
            Chưa có tìm kiếm thật. Kết quả bên dưới lấy từ vài mục mẫu để thử luồng mở điều luật.
          </p>

          {!outcome && !hint && (
            <p className="chat-status">Nhập từ khóa rồi bấm Tìm để xem kết quả.</p>
          )}

          {outcome && outcome.results.length === 0 && (
            <div className="notice notice--info" role="status">
              <Icon name="info" size={18} />
              <div>
                <p className="notice__title">Không có kết quả</p>
                <p>Không có mục mẫu nào khớp với “{outcome.keyword}”. Thử từ khóa khác.</p>
              </div>
            </div>
          )}

          {outcome && outcome.results.length > 0 && (
            <>
              <p className="search-count" role="status">
                {outcome.results.length} kết quả cho “{outcome.keyword}”
              </p>
              <ul className="results">
                {outcome.results.map((r) => (
                  <li key={`${r.document_id}/${r.article_id}`} className="result">
                    <h3 className="result__article">{r.article}</h3>
                    <p className="result__doc">{r.document_title}</p>
                    <p className="result__excerpt">{r.excerpt}</p>
                    {r.note && <p className="result__note">{r.note}</p>}
                    <Link
                      className="citation__open"
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
