"""Tách văn bản Doanh nghiệp thành chunk theo Điều/Khoản.

chunk_id theo docs/team1_data/metadata-specification.md mục 4.4:
{document_id}__{article_id}__k{số Khoản hoặc 0}__{chunk_index}
"""

import collections
import json
import re
import sys
import unicodedata
from pathlib import Path

# Console Windows mặc định cp1252, không in được tiếng Việt trong tên văn bản
# và trong cảnh báo. Không đổi encoding của file xuất, chỉ của stdout.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
INTERIM = ROOT / "interim"
REGISTRY = ROOT / "registry" / "documents.json"
OUT = ROOT / "processed" / "chunks.jsonl"

RE_CHAPTER = re.compile(r"^(Chương|CHƯƠNG)\s+([IVXLCDM]+)\b\.?\s*(.*)$")
RE_SECTION = re.compile(r"^(Mục|MỤC)\s+(\d+)\b\.?\s*(.*)$")
RE_ARTICLE = re.compile(r"^Điều\s+(\d+[a-z]?)[.:]\s*(.*)$")  # một số bản gốc ghi "Điều 122:"
RE_CLAUSE = re.compile(r"^(\d{1,2}[a-z]?)\.\s+(\S.*)$")
RE_FOOTNOTE = re.compile(r"^\[\d+\]\s+")
RE_STOP = re.compile(
    r"^(CHỦ TỊCH|CHỦ NHIỆM|BỘ TRƯỞNG|TM\. CHÍNH PHỦ|KT\. THỦ TƯỚNG|PHÓ THỦ TƯỚNG)\b"
    r"|^Luật này được Quốc hội\b"
    r"|^Nghị định này được Chính phủ\b"
    # Khối chữ ký thừa lệnh/ký thay/thay mặt của thông tư, nghị định ("KT. BỘ TRƯỞNG", "TM. ỦY BAN…").
    r"|^(KT|TM|TL|Q)\.\s"
    # Tiêu đề phụ lục (chữ hoa) mở đầu biểu mẫu, điều lệ mẫu sau phần quy phạm.
    r"|^PHỤ LỤC\b"
)
RE_CHUNK_ID = re.compile(r"^[A-Za-z0-9_-]+$")

# Bản HTML của VBHN 67/VBHN-VPQH chèn một dấu cách vào giữa bốn từ, ví dụ
# "cử ngườ i khác" thay vì "cử người khác". Dò bằng phép thử tần số trên chính
# corpus — mảnh bên trái ("ngườ") chỉ xuất hiện đúng số lần bị lỗi, trong khi từ
# đúng ("người") xuất hiện hàng nghìn lần — rồi soát tay từng chỗ. Không mở rộng
# danh sách này bằng cách đoán; `report_split_words` ở dưới sẽ cảnh báo nếu nguồn
# mới có mẫu lỗi khác.
SPLIT_WORDS = (
    ("ngườ i", "người"),
    ("Ngườ i", "Người"),
    ("dướ i", "dưới"),
    ("T rong", "Trong"),
)
RE_SPLIT_WORDS = tuple(
    (re.compile(r"\b" + re.escape(bad) + r"\b"), good) for bad, good in SPLIT_WORDS
)

# Chú thích hợp nhất: dòng định nghĩa "[n] <nội dung>" nằm ở cuối file (đã bị
# RE_FOOTNOTE chặn, không vào content), còn marker "[n]" nằm rải trong thân Điều
# và trong tên Điều. Marker mang thông tin thật — Khoản này đã bị văn bản nào sửa
# — nên được chuyển sang `amendment_notes` thay vì xóa trắng.
RE_FOOTNOTE_DEF = re.compile(r"^\[(\d+)\]\s+(\S.*)$")
RE_FOOTNOTE_MARK = re.compile(r"\s*\[(\d{1,2})\]")
MISSING_NOTE = "(chú thích hợp nhất không có trong bản đã thu)"


def repair_split_words(line: str) -> str:
    """Nối lại các từ bị chèn dấu cách. Chỉ 4 cặp ở SPLIT_WORDS."""
    for pattern, good in RE_SPLIT_WORDS:
        line = pattern.sub(good, line)
    return line


def read_footnotes(text: str) -> dict[str, str]:
    """Đọc các dòng định nghĩa chú thích hợp nhất ở cuối văn bản."""
    notes = {}
    for line in text.split("\n"):
        found = RE_FOOTNOTE_DEF.match(line.strip())
        if found:
            notes[found.group(1)] = found.group(2).strip()
    return notes


def strip_footnote_marks(text: str) -> tuple[str, list[str]]:
    """Bỏ marker [n] khỏi text, trả về text sạch và danh sách số chú thích."""
    nums = [m.group(1) for m in RE_FOOTNOTE_MARK.finditer(text)]
    if not nums:
        return text, []
    return RE_FOOTNOTE_MARK.sub("", text), nums


def report_split_words(docs: dict[str, str]) -> None:
    """Cảnh báo nếu còn mẫu 'dấu cách chen giữa từ' mà SPLIT_WORDS chưa biết.

    Mảnh bên trái phải hiếm và nối lại phải ra một từ phổ biến — cùng phép thử
    đã dùng để dò ra SPLIT_WORDS, chạy lại mỗi lần build để nguồn mới không
    lọt lỗi im lặng.
    """
    word = re.compile(r"[^\W\d_]+", re.UNICODE)
    freq = collections.Counter()
    for text in docs.values():
        freq.update(w.lower() for w in word.findall(text))
    stray = collections.Counter()
    for doc, text in docs.items():
        for line in text.split("\n"):
            spans = [(m.group(0), m.start(), m.end()) for m in word.finditer(line)]
            for (a, _, ea), (b, sb, _) in zip(spans, spans[1:]):
                if line[ea:sb] != " ":
                    continue
                joined = (a + b).lower()
                if freq[joined] >= 5 and freq[joined] >= 10 * freq[a.lower()]:
                    stray[(doc, a, b)] += 1
    if stray:
        print("CẢNH BÁO: còn từ bị chèn dấu cách mà SPLIT_WORDS chưa xử lý:")
        for (doc, a, b), n in stray.most_common():
            print(f"  {doc}: {a!r} + {b!r} -> {(a + b)!r}  x{n}")

# Bản HTML của VBHN 67/VBHN-VPQH không giữ dòng tiêu đề Chương/Mục, nên
# chapter/section được bù theo article_id từ Luật 59/2020/QH14 — hai văn bản
# dùng cùng hệ thống số Điều. Chỉ bù metadata cấu trúc, không đổi content.
STRUCTURE_FROM = {"vbhn-67-vbhn-vpqh-v1": "luat-59-2020-qh14-v1"}

PREFIX = {
    "luat": "luat",
    "nghi_dinh": "nd",
    "thong_tu": "tt",
    "van_ban_hop_nhat": "vbhn",
    "bo_luat": "bl",
}


def normalize_number(number: str) -> str:
    text = number.replace("Đ", "D").replace("đ", "d")
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[/\s]+", "-", text)
    text = re.sub(r"[^a-z0-9-]", "", text)
    return re.sub(r"-{2,}", "-", text).strip("-")


def document_ids(meta: dict) -> tuple[str, str]:
    prefix = PREFIX[meta["document_type"]]
    document_key = f"{prefix}-{normalize_number(meta['document_number'])}"
    return document_key, f"{document_key}-v1"


def token_count(text: str) -> int:
    return max(1, len(re.findall(r"\S+", text)))


def build_context_header(chunk: dict) -> str:
    """context_header theo docs/team1_data/chunk-format-spec.md mục 4."""
    parts = [f"{chunk['document_title']} {chunk['document_number']}"]
    for level, title in (("chapter", "chapter_title"), ("section", "section_title")):
        if chunk[level]:
            bit = chunk[level]
            if chunk[title]:
                bit += f". {chunk[title]}"
            parts.append(bit)
    dieu = chunk["article"]
    if chunk["article_title"]:
        dieu += f". {chunk['article_title']}"
    parts.append(dieu)
    return " > ".join(parts)


def finalize(chunk: dict) -> dict:
    chunk["context_header"] = build_context_header(chunk)
    chunk["token_count"] = token_count(chunk["context_header"] + "\n" + chunk["content"])
    return chunk


def backfill_structure(targets: list[dict], source: list[dict]) -> int:
    """Lấp chapter/section cho targets theo article_id của source."""
    table = {}
    for chunk in source:
        table.setdefault(
            chunk["article_id"],
            (
                chunk["chapter"],
                chunk["chapter_title"],
                chunk["section"],
                chunk["section_title"],
            ),
        )
    filled = 0
    missing = set()
    for chunk in targets:
        if chunk["chapter"]:
            continue
        found = table.get(chunk["article_id"])
        if not found:
            missing.add(chunk["article_id"])
            continue
        (
            chunk["chapter"],
            chunk["chapter_title"],
            chunk["section"],
            chunk["section_title"],
        ) = found
        finalize(chunk)
        filled += 1
    if missing:
        print(f"  no match for {len(missing)} articles: {sorted(missing)}")
    return filled


def is_structural(line: str) -> bool:
    return bool(
        RE_CHAPTER.match(line)
        or RE_SECTION.match(line)
        or RE_ARTICLE.match(line)
        or RE_CLAUSE.match(line)
        or RE_FOOTNOTE.match(line)
        or RE_STOP.match(line)
    )


class Parser:
    def __init__(self, meta: dict, footnotes: dict[str, str] | None = None):
        self.meta = meta
        self.footnotes = footnotes or {}
        self.file_id = meta["document_id"]
        self.document_key, self.document_id = document_ids(meta)
        self.effective_date = meta["effective_date"] or meta["issued_date"]
        self.chapter = None
        self.chapter_title = None
        self.section = None
        self.section_title = None
        self.pending = None
        self.article = None
        self.chunks = []
        self.stopped = False
        self.seen_articles = 0

    def feed(self, line: str) -> None:
        if self.stopped:
            return
        if not line:
            if self.article and self.article["buf"]:
                self.article["buf"].append("")
            return
        if RE_FOOTNOTE.match(line) or RE_STOP.match(line):
            self.flush_article()
            self.stopped = True
            return
        if self.pending and not is_structural(line):
            kind = self.pending
            self.pending = None
            if kind == "chapter":
                self.chapter_title = line
            else:
                self.section_title = line
            return
        self.pending = None

        chapter = RE_CHAPTER.match(line)
        if chapter:
            self.flush_article()
            self.chapter = chapter.group(2)
            self.chapter_title = chapter.group(3).strip() or None
            self.section = None
            self.section_title = None
            if not self.chapter_title:
                self.pending = "chapter"
            return

        section = RE_SECTION.match(line)
        if section:
            self.flush_article()
            self.section = section.group(2)
            self.section_title = section.group(3).strip() or None
            if not self.section_title:
                self.pending = "section"
            return

        article = RE_ARTICLE.match(line)
        if article:
            # Số Điều quay lại 1 sau khi đã có Điều khác: đó là mẫu quyết định/điều lệ mẫu trong phụ lục,
            # không phải phần quy phạm của văn bản. Dừng để không sinh chunk_id trùng.
            if article.group(1) == "1" and self.seen_articles:
                self.flush_article()
                self.stopped = True
                return
            self.seen_articles += 1
            self.flush_article()
            self.article = {
                "num": article.group(1),
                "title": article.group(2).strip(),
                "intro": [],
                "clauses": [],
                "buf": [],
            }
            return

        if self.article:
            clause = RE_CLAUSE.match(line)
            if clause and self._accept_clause(clause.group(1)):
                self._close_buf()
                self.article["clauses"].append({"num": clause.group(1), "lines": [line]})
                return
            self.article["buf"].append(line)

    def _accept_clause(self, num: str) -> bool:
        match = re.match(r"(\d+)([a-z]?)$", num)
        if not match:
            return False
        number, suffix = int(match.group(1)), match.group(2)
        clauses = self.article["clauses"]
        if not clauses:
            return number == 1
        last = re.match(r"(\d+)([a-z]?)$", clauses[-1]["num"])
        last_n, last_s = int(last.group(1)), last.group(2)
        if number > last_n:
            return True
        return number == last_n and suffix > last_s

    def _close_buf(self) -> None:
        buf = self.article["buf"]
        self.article["buf"] = []
        text = "\n".join(buf).strip()
        if not text:
            return
        if self.article["clauses"]:
            self.article["clauses"][-1]["lines"].extend(buf)
        else:
            self.article["intro"].extend(buf)

    def flush_article(self) -> None:
        if not self.article:
            return
        self._close_buf()
        art = self.article
        self.article = None
        dieu = f"Điều {art['num']}"
        if art["title"]:
            dieu += f". {art['title']}"
        intro = "\n".join(art["intro"]).strip()
        if not art["clauses"]:
            body = intro or dieu
            self._emit(art["num"], None, dieu, body)
            return
        for clause in art["clauses"]:
            text = "\n".join(clause["lines"]).strip()
            if intro:
                text = intro + "\n\n" + text
            self._emit(art["num"], clause["num"], dieu, text)

    def _emit(self, art_num: str, clause_num: str | None, dieu: str, body: str) -> None:
        article_id = f"dieu-{art_num.lower()}"
        k = clause_num or "0"
        chunk_index = 0
        chunk_id = f"{self.document_id}__{article_id}__k{k}__{chunk_index}"
        article = f"Điều {art_num}"
        article_title = dieu.split(". ", 1)[1] if ". " in dieu else ""
        body, body_marks = strip_footnote_marks(body)
        article_title, title_marks = strip_footnote_marks(article_title)
        seen = dict.fromkeys(body_marks + title_marks)
        notes = [f"[{n}] {self.footnotes.get(n) or MISSING_NOTE}" for n in seen]
        self.chunks.append(
            finalize({
                "chunk_id": chunk_id,
                "document_id": self.document_id,
                "document_key": self.document_key,
                "article_id": article_id,
                "version": "v1",
                "document_title": self.meta["document_title"],
                "document_number": self.meta["document_number"],
                "document_type": self.meta["document_type"],
                "issuing_authority": self.meta["issuing_authority"],
                "issued_date": self.meta["issued_date"],
                "effective_date": self.effective_date,
                "expiry_date": None,
                "legal_status": self.meta["legal_status"],
                "source_url": self.meta["source_url"],
                "part": None,
                "chapter": f"Chương {self.chapter}" if self.chapter else None,
                "chapter_title": self.chapter_title,
                "section": f"Mục {self.section}" if self.section else None,
                "section_title": self.section_title,
                "article": article,
                "article_title": article_title,
                "clause": f"Khoản {clause_num}" if clause_num else None,
                "point": None,
                "content": body,
                "context_header": "",
                "chunk_index": chunk_index,
                "chunk_count": 1,
                "token_count": 0,
                "amended_by": [],
                "amendment_notes": notes,
                "pipeline_version": "1.0.0",
            })
        )


def main() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    all_chunks = []
    by_document = {}
    sources = {}
    for meta in registry:
        path = INTERIM / f"{meta['document_id']}.txt"
        text = path.read_text(encoding="utf-8")
        lines = [repair_split_words(line.strip()) for line in text.splitlines()]
        # Báo cáo chạy trên text đã sửa, nên chỉ cảnh báo mẫu lỗi MỚI.
        sources[meta["document_id"]] = "\n".join(lines)
        parser = Parser(meta, read_footnotes(text))
        for line in lines:
            parser.feed(line)
        parser.flush_article()
        ids = [c["chunk_id"] for c in parser.chunks]
        bad = [i for i in ids if not RE_CHUNK_ID.match(i)]
        if bad:
            raise SystemExit(f"chunk_id sai mẫu metadata spec: {bad[:5]}")
        if len(ids) != len(set(ids)):
            dup = sorted({i for i in ids if ids.count(i) > 1})
            raise SystemExit(f"duplicate chunk_id in {meta['document_id']}: {dup[:8]}")
        by_document[parser.document_id] = parser.chunks
        all_chunks.extend(parser.chunks)
        print(f"{parser.document_id}: {len(parser.chunks)} chunks")

    for target_id, source_id in STRUCTURE_FROM.items():
        if target_id not in by_document or source_id not in by_document:
            continue
        print(f"backfill chapter/section: {target_id} <- {source_id}")
        filled = backfill_structure(by_document[target_id], by_document[source_id])
        print(f"  filled {filled} chunks")

    report_split_words(sources)

    global_ids = [c["chunk_id"] for c in all_chunks]
    if len(global_ids) != len(set(global_ids)):
        raise SystemExit("chunk_id trùng giữa các văn bản")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="\n") as fh:
        for chunk in all_chunks:
            fh.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    print(f"wrote {len(all_chunks)} -> {OUT}")


if __name__ == "__main__":
    main()
