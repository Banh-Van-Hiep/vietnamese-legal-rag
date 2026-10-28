// Hàm thuần cho phần hiển thị căn cứ pháp lý (VLRA-43). Không gọi mạng, không tạo ID:
// mọi ID văn bản/điều luôn lấy từ citation đã được kiểm tra theo contract.
import type { Citation } from "../types";

/** "Điều 17, Khoản 2, Điểm a": nhãn hiển thị theo đúng thứ tự Điều → Khoản → Điểm. */
export function citationLocation(c: Pick<Citation, "article" | "clause" | "point">): string {
  return [c.article, c.clause, c.point].filter((part): part is string => !!part && part.trim() !== "").join(", ");
}

/** Phần khoản/điểm được trích, bỏ phần Điều (Viewer đã hiển thị Điều ở tiêu đề). */
export function citedUnitLabel(c: Pick<Citation, "clause" | "point">): string {
  return [c.clause, c.point].filter((part): part is string => !!part && part.trim() !== "").join(", ");
}

export interface TextRange {
  start: number;
  end: number;
}

interface Line {
  text: string;
  start: number;
  end: number;
}

function linesOf(content: string): Line[] {
  const lines: Line[] = [];
  let start = 0;
  for (const text of content.split("\n")) {
    lines.push({ text, start, end: start + text.length });
    start += text.length + 1;
  }
  return lines;
}

const CLAUSE_LINE = /^\s*(\d+)\.\s/;
// Điểm trong văn bản pháp luật Việt Nam: a) b) c) d) đ) e)…
const POINT_LINE = /^\s*([a-zđ])\)\s/i;

/** Tìm đúng một dòng bắt đầu đơn vị; trả null nếu không có hoặc có nhiều hơn một (không đoán). */
function uniqueStart(lines: Line[], from: number, to: number, matches: (text: string) => boolean): number | null {
  let found: number | null = null;
  for (let i = from; i < to; i++) {
    if (!matches(lines[i].text)) continue;
    if (found !== null) return null;
    found = i;
  }
  return found;
}

/** Dòng kết thúc (không gồm) của đơn vị bắt đầu tại `first`: trước dòng bắt đầu đơn vị cùng cấp hoặc cao hơn. */
function unitEnd(lines: Line[], first: number, to: number, isBoundary: (text: string) => boolean): number {
  for (let i = first + 1; i < to; i++) {
    if (isBoundary(lines[i].text)) return i;
  }
  return to;
}

function trimRange(lines: Line[], first: number, endExclusive: number): TextRange {
  let last = endExclusive - 1;
  while (last > first && lines[last].text.trim() === "") last--;
  return { start: lines[first].start, end: lines[last].end };
}

/**
 * Xác định vị trí khoản/điểm được trích trong nguyên văn Điều.
 * Chỉ trả kết quả khi nhãn có dạng chuẩn ("Khoản 2", "Điểm a") và vị trí là duy nhất;
 * trường hợp còn lại trả null để giao diện không tô sai chỗ (team3.md §2.4).
 */
export function locateCitedUnit(content: string, clause: string | null, point: string | null): TextRange | null {
  if (!clause && !point) return null;
  const clauseNo = clause ? /^\s*khoản\s+(\d+)\s*$/i.exec(clause)?.[1] : undefined;
  const pointLetter = point ? /^\s*điểm\s+([a-zđ])\s*$/i.exec(point)?.[1]?.toLowerCase() : undefined;
  if ((clause && !clauseNo) || (point && !pointLetter)) return null;

  const lines = linesOf(content);
  let from = 0;
  let to = lines.length;

  if (clauseNo) {
    const first = uniqueStart(lines, 0, lines.length, (text) => CLAUSE_LINE.exec(text)?.[1] === clauseNo);
    if (first === null) return null;
    from = first;
    to = unitEnd(lines, first, lines.length, (text) => CLAUSE_LINE.test(text));
    if (!pointLetter) return trimRange(lines, from, to);
  }

  const first = uniqueStart(lines, from, to, (text) => POINT_LINE.exec(text)?.[1]?.toLowerCase() === pointLetter);
  if (first === null) return null;
  const end = unitEnd(lines, first, to, (text) => POINT_LINE.test(text) || CLAUSE_LINE.test(text));
  return trimRange(lines, first, end);
}

/** Bản sao chép câu trả lời kèm danh sách căn cứ, để dán sang nơi khác vẫn đối chiếu được. */
export function answerWithSources(answer: string, citations: Citation[]): string {
  if (citations.length === 0) return answer;
  const sources = citations.map(
    (c) => `[${c.citation_id}] ${citationLocation(c)} — ${c.document_title}. Nguồn: ${c.source_url}`,
  );
  return `${answer}\n\nCăn cứ pháp lý:\n${sources.join("\n")}`;
}

/** Link sang trang xem riêng, giữ thông tin khoản/điểm để tô sáng khi mở lại hoặc chia sẻ. */
export function documentPageHref(c: Pick<Citation, "document_id" | "article_id" | "clause" | "point" | "citation_id">): string {
  const query = new URLSearchParams({ articleId: c.article_id });
  if (c.clause) query.set("clause", c.clause);
  if (c.point) query.set("point", c.point);
  query.set("cite", c.citation_id);
  return `/documents/${encodeURIComponent(c.document_id)}?${query.toString()}`;
}
