// Danh sách trích dẫn của một câu trả lời.
import type { Citation } from "../../types";
import Icon from "../common/Icon";
import CitationCard from "./CitationCard";

interface Props {
  citations: Citation[];
}

export default function CitationList({ citations }: Props) {
  return (
    <details className="citations" open>
      <summary className="citations__summary">
        <Icon name="scale" size={16} />
        Căn cứ pháp lý ({citations.length})
        <Icon name="chevronDown" size={15} />
      </summary>
      <ol className="citations__list">
        {citations.map((c, i) => (
          <li key={c.chunkId}>
            <CitationCard citation={c} index={i + 1} />
          </li>
        ))}
      </ol>
    </details>
  );
}
