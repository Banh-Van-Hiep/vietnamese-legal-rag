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
    <details className="group mt-1.5" open data-testid="citations">
      <summary className="-ml-2 inline-flex cursor-pointer list-none items-center gap-2 rounded-lg py-1.5 pr-2.5 pl-2 text-[14px] font-semibold text-ink-700 select-none hover:bg-paper [&::-webkit-details-marker]:hidden">
        <span className="inline-flex text-seal">
          <Icon name="scale" size={16} />
        </span>
        Căn cứ pháp lý ({citations.length})
        <span className="inline-flex text-faint transition-transform duration-[160ms] group-open:rotate-180">
          <Icon name="chevronDown" size={15} />
        </span>
      </summary>
      <ol className="mt-2 flex flex-col gap-2.5">
        {citations.map((c) => (
          <li key={c.citation_id}>
            <CitationCard citation={c} onOpen={onOpen} />
          </li>
        ))}
      </ol>
    </details>
  );
}
