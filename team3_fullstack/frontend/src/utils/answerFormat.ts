// Phân tích câu trả lời thành khối/đoạn để hiển thị an toàn (VLRA-43, Docs v2.0 §8.7).
// Không render HTML từ LLM: chỉ nhận dạng một số cú pháp văn bản đơn giản rồi để React escape.
//   - đoạn cách nhau bởi dòng trống; tiêu đề là đoạn chỉ có một cụm **đậm**
//   - danh sách "- ", "1. ", "a) " khi mọi dòng của đoạn cùng một kiểu
//   - **đậm** và dấu tham chiếu [C1] trong dòng

export type Inline =
  | { kind: "text"; text: string }
  | { kind: "bold"; text: string }
  | { kind: "cite"; citationId: string };

export type Block =
  | { kind: "heading"; text: string }
  | { kind: "paragraph"; lines: Inline[][] }
  | { kind: "bullets"; items: Inline[][] }
  | { kind: "numbered"; items: { marker: string; content: Inline[] }[] };

const NUMBERED = /^(\d+)\.\s+(.*)$/;
const LETTERED = /^([a-zđ])\)\s+(.*)$/i;

export function parseInline(text: string): Inline[] {
  const parts: Inline[] = [];
  for (const piece of text.split(/(\*\*[^*\n]+\*\*|\[C\d+\])/g)) {
    if (!piece) continue;
    const cite = /^\[(C\d+)\]$/.exec(piece);
    if (cite) parts.push({ kind: "cite", citationId: cite[1] });
    else if (piece.length > 4 && piece.startsWith("**") && piece.endsWith("**")) parts.push({ kind: "bold", text: piece.slice(2, -2) });
    else parts.push({ kind: "text", text: piece });
  }
  return parts;
}

export function parseAnswer(answer: string): Block[] {
  const blocks: Block[] = [];
  const normalized = answer.replace(/\r\n?/g, "\n").trim();
  if (!normalized) return blocks;
  for (const raw of normalized.split(/\n\s*\n/)) {
    const lines = raw.split("\n").map((l) => l.trimEnd()).filter((l) => l.trim() !== "");
    if (lines.length === 0) continue;
    const trimmed = lines.map((l) => l.trim());

    if (trimmed.length === 1 && /^\*\*[^*\n]+\*\*$/.test(trimmed[0])) {
      blocks.push({ kind: "heading", text: trimmed[0].slice(2, -2) });
      continue;
    }
    // Một dòng dẫn rồi tới danh sách ("Cần chuẩn bị:" + "1. …"): tách dòng dẫn thành đoạn riêng.
    const whole = listBlock(trimmed);
    const afterLead = whole === null && trimmed.length > 2 ? listBlock(trimmed.slice(1)) : null;
    if (whole) {
      blocks.push(whole);
    } else if (afterLead) {
      blocks.push({ kind: "paragraph", lines: [parseInline(trimmed[0])] }, afterLead);
    } else {
      blocks.push({ kind: "paragraph", lines: trimmed.map(parseInline) });
    }
  }
  return blocks;
}

/** Danh sách khi mọi dòng cùng một kiểu: "- ", "1. " hoặc "a) "; ngược lại null. */
function listBlock(lines: string[]): Block | null {
  if (lines.length === 0) return null;
  if (lines.every((l) => l.startsWith("- "))) return { kind: "bullets", items: lines.map((l) => parseInline(l.slice(2))) };
  const pattern = lines.every((l) => NUMBERED.test(l)) ? NUMBERED : lines.every((l) => LETTERED.test(l)) ? LETTERED : null;
  if (!pattern) return null;
  return {
    kind: "numbered",
    items: lines.map((l) => {
      const m = pattern.exec(l)!;
      return { marker: pattern === NUMBERED ? `${m[1]}.` : `${m[1]})`, content: parseInline(m[2]) };
    }),
  };
}
