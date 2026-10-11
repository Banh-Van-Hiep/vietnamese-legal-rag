"""Tách văn bản Doanh nghiệp thành chunk theo Điều/Khoản.

chunk_id theo docs/team1_data/metadata-specification.md mục 4.4:
{document_id}__{article_id}__k{số Khoản hoặc 0}__{chunk_index}
"""

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INTERIM = ROOT / "interim"
REGISTRY = ROOT / "registry" / "documents.json"
OUT = ROOT / "processed" / "chunks.jsonl"

RE_CHAPTER = re.compile(r"^(Chương|CHƯƠNG)\s+([IVXLCDM]+)\b\.?\s*(.*)$")
RE_SECTION = re.compile(r"^(Mục|MỤC)\s+(\d+)\b\.?\s*(.*)$")
RE_ARTICLE = re.compile(r"^Điều\s+(\d+[a-z]?)\.\s*(.*)$")
RE_CLAUSE = re.compile(r"^(\d{1,2}[a-z]?)\.\s+(\S.*)$")
RE_FOOTNOTE = re.compile(r"^\[\d+\]\s+")
RE_STOP = re.compile(
    r"^(CHỦ TỊCH|CHỦ NHIỆM|BỘ TRƯỞNG|TM\. CHÍNH PHỦ|KT\. THỦ TƯỚNG|PHÓ THỦ TƯỚNG)\b"
    r"|^Luật này được Quốc hội\b"
    r"|^Nghị định này được Chính phủ\b"
)
RE_CHUNK_ID = re.compile(r"^[A-Za-z0-9_-]+$")
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
    def __init__(self, meta: dict):
        self.meta = meta
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

    def chapter_label(self) -> str | None:
        if not self.chapter:
            return None
        label = f"Chương {self.chapter}"
        if self.chapter_title:
            label += f". {self.chapter_title}"
        if self.section:
            label += f" > Mục {self.section}"
            if self.section_title:
                label += f". {self.section_title}"
        return label

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
        chuong = self.chapter_label()
        if not art["clauses"]:
            body = intro or dieu
            self._emit(art["num"], None, dieu, chuong, body)
            return
        for clause in art["clauses"]:
            text = "\n".join(clause["lines"]).strip()
            if intro:
                text = intro + "\n\n" + text
            self._emit(art["num"], clause["num"], dieu, chuong, text)

    def _emit(self, art_num: str, clause_num: str | None, dieu: str, chuong, body: str) -> None:
        article_id = f"dieu-{art_num.lower()}"
        k = clause_num or "0"
        chunk_index = 0
        chunk_id = f"{self.document_id}__{article_id}__k{k}__{chunk_index}"
        article = f"Điều {art_num}"
        article_title = dieu.split(". ", 1)[1] if ". " in dieu else ""
        parts = [f"{self.meta['document_title']} {self.meta['document_number']}"]
        if self.chapter:
            chapter_bit = f"Chương {self.chapter}"
            if self.chapter_title:
                chapter_bit += f". {self.chapter_title}"
            parts.append(chapter_bit)
        if self.section:
            section_bit = f"Mục {self.section}"
            if self.section_title:
                section_bit += f". {self.section_title}"
            parts.append(section_bit)
        parts.append(dieu)
        context_header = " > ".join(parts)
        counted = token_count(context_header + "\n" + body)
        self.chunks.append(
            {
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
                "context_header": context_header,
                "chunk_index": chunk_index,
                "chunk_count": 1,
                "token_count": counted,
                "amended_by": [],
                "amendment_notes": [],
                "pipeline_version": "1.0.0",
            }
        )


def main() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    all_chunks = []
    for meta in registry:
        path = INTERIM / f"{meta['document_id']}.txt"
        parser = Parser(meta)
        for line in path.read_text(encoding="utf-8").splitlines():
            parser.feed(line.strip())
        parser.flush_article()
        ids = [c["chunk_id"] for c in parser.chunks]
        bad = [i for i in ids if not RE_CHUNK_ID.match(i)]
        if bad:
            raise SystemExit(f"chunk_id sai mẫu metadata spec: {bad[:5]}")
        if len(ids) != len(set(ids)):
            dup = sorted({i for i in ids if ids.count(i) > 1})
            raise SystemExit(f"duplicate chunk_id in {meta['document_id']}: {dup[:8]}")
        all_chunks.extend(parser.chunks)
        print(f"{meta['document_id']}: {len(parser.chunks)} chunks")

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
