// Danh sách trích dẫn của một câu trả lời.
import type { Citation } from "../../types";
import Icon from "../common/Icon";
import CitationCard from "./CitationCard";

interface Props {
  citations: Citation[];
  onOpen: (citation: Citation) => void;
}

export default function CitationList({ citations, onOpen }: Props) {
  return (
    <details className="citations" open>
      <summary className="citations__summary">
        <Icon name="scale" size={16} />
        Căn cứ pháp lý ({citations.length})
        <Icon name="chevronDown" size={15} />
      </summary>
      <ol className="citations__list">
        {citations.map((c) => (
          <li key={c.citation_id}>
            <CitationCard citation={c} onOpen={onOpen} />
          </li>
        ))}
      </ol>
    </details>
  );
}
