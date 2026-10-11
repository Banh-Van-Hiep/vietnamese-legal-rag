// Một trích dẫn. Nội dung điều luật được tải theo ID khi người dùng mở, không nhúng sẵn trong câu trả lời.
import type { Citation } from "../../types";

interface Props {
  citation: Citation;
  onOpen: (citation: Citation) => void;
}

export default function CitationCard({ citation, onOpen }: Props) {
  const location = [citation.article, citation.clause, citation.point].filter(Boolean).join(", ");
  return (
    <article className="citation">
      <header className="citation__head">
        <span className="citation__index">{citation.citation_id.replace(/^C/, "")}</span>
        <div>
          <h3 className="citation__article">{location}</h3>
          <p className="citation__doc">{citation.document_title}</p>
        </div>
      </header>
      <button className="citation__open" type="button" onClick={() => onOpen(citation)}>
        Xem nguyên văn điều luật
      </button>
    </article>
  );
}
