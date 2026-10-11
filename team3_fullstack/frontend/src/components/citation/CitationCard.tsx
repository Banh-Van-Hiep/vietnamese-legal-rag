// Một trích dẫn.
import type { Citation } from "../../types";

interface Props {
  citation: Citation;
  index: number;
}

export default function CitationCard({ citation, index }: Props) {
  return (
    <article className="citation">
      <header className="citation__head">
        <span className="citation__index">{index}</span>
        <div>
          <h3 className="citation__article">{citation.article}</h3>
          <p className="citation__doc">{citation.documentTitle}</p>
        </div>
      </header>
      <blockquote className="citation__snippet">{citation.snippet}</blockquote>
      <button className="citation__open" type="button">
        Xem nguyên văn điều luật
      </button>
    </article>
  );
}
