# BM25 Proposal

## 1. Mục tiêu

Chọn thư viện BM25 và cấu hình xử lý tiếng Việt cho nhánh tìm kiếm từ khóa
(lexical) trong [Retrieval Design](retrieval-design.md).

BM25 chấm điểm chunk theo mức độ trùng **từ** với câu hỏi: từ càng hiếm trong
corpus (IDF cao) và xuất hiện càng nhiều trong chunk thì điểm càng cao, có điều
chỉnh theo độ dài chunk. BM25 mạnh với số hiệu văn bản, số Điều và thuật ngữ
pháp lý chính xác — những thứ mô hình embedding hay bỏ sót.

## 2. Lựa chọn thư viện

| Tiêu chí | `bm25s` | `rank_bm25` | Elasticsearch / OpenSearch | Sparse vector Qdrant |
|---|---|---|---|---|
| Cài đặt | `pip`, chỉ cần NumPy + SciPy | `pip`, thuần Python | Server JVM riêng | Dùng Qdrant sẵn có |
| Tốc độ truy vấn | Rất nhanh (tính sẵn điểm vào sparse matrix) | Chậm, tính lại mỗi truy vấn | Nhanh | Nhanh |
| Biến thể BM25 | Lucene (mặc định), Robertson, ATIRE, BM25L, BM25+ | Okapi, BM25L, BM25+ | Lucene | Tự tính TF phía client |
| Lưu / nạp index | Có (`save` / `load`, hỗ trợ mmap) | Không, phải pickle | Có | Có |
| Tokenizer tùy biến | Nhận list token đã tách sẵn | Nhận list token | Cần plugin analyzer tiếng Việt | Phải tự tính trọng số |

**Chọn `bm25s`** với `method="lucene"`:

- Nhanh và nhẹ, đủ cho corpus vài nghìn đến vài trăm nghìn chunk.
- Nhận token đã tách sẵn, nên toàn quyền dùng tokenizer tiếng Việt riêng.
- Biến thể Lucene giống Elasticsearch, kết quả dễ đối chiếu với tài liệu tham khảo.
- Lưu index ra file, khởi động service chỉ cần nạp lại, không build lại.

## 3. Xử lý text tiếng Việt cho BM25

BM25 chỉ tốt khi **văn bản và câu hỏi được tách từ giống hệt nhau**. Toàn bộ
các bước dưới đây đóng gói trong **một hàm duy nhất** `tokenize_vi(text)`, dùng
chung cho cả indexing và truy vấn.

```text
search_text / question
   │
   ├─ [T1] Unicode NFC
   ├─ [T2] Chữ thường
   ├─ [T3] Thống nhất vị trí dấu thanh
   ├─ [T4] Bảo vệ cụm pháp lý (số hiệu, Điều/Khoản/Điểm)
   ├─ [T5] Tách từ tiếng Việt (word segmentation)
   ├─ [T6] Bỏ token chỉ gồm dấu câu
   └─ [T7] (Tùy chọn) bỏ stopword
   ▼
list[str] token
```

### 3.1. Vì sao phải tách từ

Tiếng Việt viết cách nhau theo **âm tiết**, không theo **từ**. "lao động"
là một từ gồm hai âm tiết. Nếu tách theo dấu cách, "lao" và "động" thành hai
token rời, BM25 sẽ khớp cả những chunk chứa "động" trong "hoạt động", "biến
động", "bất động sản". Tách từ đúng cho ra token `lao_động`, chính xác hơn.

### 3.2. So sánh công cụ tách từ

| Tiêu chí | Underthesea | PyVi | Tách theo âm tiết (dấu cách) |
|---|---|---|---|
| Độ chính xác tách từ | Cao (F1 ~95,7% trên UD-VTB theo benchmark của dự án nom-vn) | Thấp hơn trong các benchmark độc lập | Không tách từ |
| Tốc độ | ~1 ms / câu | Nhanh hơn Underthesea khoảng 2 lần | Tức thì |
| Bảo trì | Đang được phát triển tích cực | Ít cập nhật | — |
| Giấy phép | Apache-2.0 | MIT | — |
| Ghi chú | API `word_tokenize(text, format="text")` trả `thành_lập doanh_nghiệp` | `ViTokenizer.tokenize(text)` cùng định dạng | Bền với lỗi tách từ nhưng kém chính xác |

**Chọn Underthesea** làm mặc định:

- Truy vấn chỉ là một câu, ~1 ms là không đáng kể so với ngân sách 1 giây.
- Indexing chạy offline, vài nghìn chunk chỉ mất vài chục giây.
- Độ chính xác tách từ ảnh hưởng trực tiếp đến chất lượng BM25.

**PyVi** và **tách theo âm tiết** được giữ làm cấu hình đối chứng trong thử
nghiệm (mục 5). Cả Underthesea (Apache-2.0) và PyVi (MIT) đều có giấy phép cho
phép dùng tự do.

### 3.3. Chi tiết từng bước

| Bước | Cách làm | Ví dụ |
|---|---|---|
| T1 | `unicodedata.normalize("NFC", text)` — phòng khi câu hỏi người dùng gõ dấu tổ hợp | — |
| T2 | `text.lower()` | `Người Lao Động` → `người lao động` |
| T3 | Quy các vần `oa`, `oe`, `uy` **ở cuối âm tiết** về một kiểu đặt dấu duy nhất (đề xuất: `oà` → `òa`, `oé` → `óe`, `uỷ` → `ủy`). Không áp dụng khi sau vần còn phụ âm (`hoàng`, `khoảng`, `huỳnh`) hoặc trước là `q` (`quý`, `quỷ`) | `hoà giải` và `hòa giải` cùng thành `hòa giải`; `hoàng` giữ nguyên |
| T4 | Thay cụm pháp lý bằng token liền khối trước khi tách từ (mục 3.4) | `Điều 113` → `điều_113` |
| T5 | `underthesea.word_tokenize(text, format="text").split()` | `nghỉ hằng năm` → `nghỉ`, `hằng_năm` |
| T6 | Bỏ token không chứa chữ hoặc số | `,` `:` `(` bị bỏ |
| T7 | **Mặc định không bỏ stopword** (IDF đã tự giảm trọng số từ phổ biến). Nếu thử nghiệm bỏ stopword, tuyệt đối giữ các từ mang nghĩa pháp lý: `không`, `chưa`, `cấm`, `nghiêm_cấm`, `phải`, `được`, `có_quyền` | Bỏ `không` sẽ biến "không có quyền" thành "có quyền" |

### 3.4. Bảo vệ cụm pháp lý

Word segmenter không biết "45/2019/QH14" là một số hiệu, có thể cắt thành nhiều
mảnh. Bước T4 dùng regex để gộp các cụm sau thành **một token** trước khi tách từ:

| Mẫu | Regex (sau T2) | Token |
|---|---|---|
| Số hiệu văn bản | `\d+/\d{4}/[a-zđ0-9-]+` | `45/2019/qh14`, `145/2020/nđ-cp` |
| Điều | `điều\s+(\d+[a-z]?)` | `điều_17`, `điều_17a` |
| Khoản | `khoản\s+(\d+)` | `khoản_2` |
| Điểm | `điểm\s+([a-zđ])\b` | `điểm_a` |
| Chương | `chương\s+([ivxlc]+)\b` | `chương_ii` |

Vì `search_text` có `context_header` chứa "Điều 113. ..." (xem Chunk Format), câu
hỏi "điều 113 bộ luật lao động" sẽ khớp chính xác token `điều_113` của các chunk
thuộc Điều 113.

### 3.5. Phác thảo code

```python
import re
import unicodedata
from underthesea import word_tokenize

TONE_MAP = {"oà": "òa", "oá": "óa", "oả": "ỏa", "oã": "õa", "oạ": "ọa",
            "oè": "òe", "oé": "óe", "oẻ": "ỏe", "oẽ": "õe", "oẹ": "ọe",
            "uỳ": "ùy", "uý": "úy", "uỷ": "ủy", "uỹ": "ũy", "uỵ": "ụy"}
# Chỉ đổi khi vần đứng cuối âm tiết và không đi sau "q": "hoàng", "quỷ" giữ nguyên.
TONE_RE = re.compile(r"(?<!q)(?:" + "|".join(TONE_MAP) + r")(?!\w)")

LEGAL_PATTERNS = [
    (re.compile(r"\d+/\d{4}/[a-zđ0-9-]+"), lambda m: m.group(0)),
    (re.compile(r"\b(điều|khoản|điểm|chương)\s+(\d+[a-z]?|[a-zđ]|[ivxlc]+)\b"),
     lambda m: f"{m.group(1)}_{m.group(2)}"),
]

def tokenize_vi(text: str) -> list[str]:
    text = unicodedata.normalize("NFC", text).lower()
    text = TONE_RE.sub(lambda m: TONE_MAP[m.group(0)], text)
    protected: dict[str, str] = {}
    for pattern, render in LEGAL_PATTERNS:
        def _protect(m):
            key = f"xlegalx{len(protected)}x"
            protected[key] = render(m)
            return f" {key} "
        text = pattern.sub(_protect, text)
    tokens = word_tokenize(text, format="text").split()
    tokens = [protected.get(t, t) for t in tokens]
    return [t for t in tokens if any(c.isalnum() for c in t)]
```

Đây là phác thảo để thống nhất hành vi. Khi triển khai, unit test tối thiểu phải gồm:

- T3: `hoà` → `hòa`, `thuỷ` → `thủy`, `uỷ ban` → `ủy ban`; giữ nguyên `hoàng`,
  `khoảng`, `toán`, `quý`, `quỷ`, `huỳnh`.
- T4: bắt được `điều 113`, `khoản 1`, `điểm đ`, `chương vii`, `45/2019/qh14`,
  `145/2020/nđ-cp`; **không** bắt `điều kiện`, `điều lệ`.

## 4. Cấu hình index và truy vấn

### 4.1. Indexing

```python
import bm25s

chunk_ids = [c["chunk_id"] for c in chunks]
corpus_tokens = [tokenize_vi(c["context_header"] + "\n" + c["content"]) for c in chunks]

retriever = bm25s.BM25(method="lucene", k1=1.2, b=0.75)
retriever.index(corpus_tokens)                       # list[list[str]]
retriever.save(f"data/index/bm25/{index_version}", corpus=chunk_ids)
```

- Chỉ index chunk có `legal_status` mặc định (Metadata Specification mục 3.2),
  nên BM25 không cần bộ lọc lúc truy vấn.
- `corpus` lưu kèm chỉ là `chunk_id`; metadata đầy đủ lấy từ chunk store.

### 4.2. Tham số

| Tham số | Giá trị khởi đầu | Ý nghĩa | Dải thử nghiệm |
|---|---:|---|---|
| `method` | `lucene` | Công thức BM25 giống Lucene/Elasticsearch | `robertson`, `bm25+` |
| `k1` | 1.2 | Mức bão hòa khi một từ lặp nhiều lần trong chunk | 0.9, 1.2, 1.5, 2.0 |
| `b` | 0.75 | Mức phạt chunk dài | 0.5, 0.75, 0.9 |
| Số candidate | 100 | Số kết quả BM25 đưa vào RRF | 50, 100, 200 |

### 4.3. Truy vấn và điểm số

- `retrieve(question, top_k, method="bm25")`: tách từ câu hỏi bằng `tokenize_vi`,
  lấy `top_k` chunk điểm cao nhất.
- Chunk có điểm BM25 = 0 (không trùng token nào) bị loại. Nếu không còn chunk
  nào thì trả `results: []` — đúng ngữ nghĩa contract "tìm thành công nhưng
  không có kết quả".
- `score` trong output là điểm BM25 thô (≥ 0, không có cận trên, không so sánh
  được giữa các câu hỏi khác nhau); `retrieval_method = "bm25"`.

## 5. Thử nghiệm

Trên bộ đánh giá chung (Retrieval Design mục 5), đo Recall@20 và MRR@10:

| Cấu hình | Tách từ | Ghi chú |
|---|---|---|
| A (mặc định) | Underthesea + bảo vệ cụm pháp lý | |
| B | PyVi + bảo vệ cụm pháp lý | So tốc độ / chất lượng |
| C | Âm tiết (tách theo dấu cách) + bảo vệ cụm pháp lý | Đối chứng không tách từ |
| D | Underthesea, **không** bảo vệ cụm pháp lý | Đo giá trị của bước T4 |
| E | Underthesea + bỏ stopword (giữ từ phủ định/pháp lý) | Đo giá trị của T7 |

Sau đó tinh chỉnh `k1`, `b` trên cấu hình tốt nhất. Tách riêng tập tinh chỉnh và
tập báo cáo để tránh overfit.
