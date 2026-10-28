import { describe, expect, it } from "vitest";
import type { Citation } from "../types";
import { answerWithSources, citationLocation, citedUnitLabel, documentPageHref, locateCitedUnit } from "./legalCitation";

// Trích Điều 17 Luật Doanh nghiệp 2020 theo đúng định dạng nguồn (dòng trống giữa các đơn vị).
const DIEU_17 = [
  "1. Tổ chức, cá nhân có quyền thành lập và quản lý doanh nghiệp tại Việt Nam theo quy định của Luật này, trừ trường hợp quy định tại khoản 2 Điều này.",
  "",
  "2. Tổ chức, cá nhân sau đây không có quyền thành lập và quản lý doanh nghiệp tại Việt Nam:",
  "",
  "a) Cơ quan nhà nước, đơn vị lực lượng vũ trang nhân dân sử dụng tài sản nhà nước để thành lập doanh nghiệp;",
  "",
  "b) Cán bộ, công chức, viên chức theo quy định của Luật Cán bộ, công chức và Luật Viên chức;",
  "",
  "đ) Người chưa thành niên; người bị hạn chế năng lực hành vi dân sự;",
  "",
  "3. Tổ chức, cá nhân có quyền góp vốn, mua cổ phần, trừ trường hợp sau đây:",
  "",
  "a) Cơ quan nhà nước sử dụng tài sản nhà nước góp vốn vào doanh nghiệp để thu lợi riêng;",
  "",
  "4. Thu lợi riêng cho cơ quan, đơn vị mình quy định tại điểm a khoản 2 và điểm a khoản 3 Điều này là việc sử dụng thu nhập.",
].join("\n");

const slice = (content: string, clause: string | null, point: string | null) => {
  const range = locateCitedUnit(content, clause, point);
  return range ? content.slice(range.start, range.end) : null;
};

const citation: Citation = {
  citation_id: "C2",
  chunk_id: "luat-59-2020-qh14-v1__dieu-17__k2__0",
  document_id: "luat-59-2020-qh14-v1",
  article_id: "dieu-17",
  document_title: "Luật Doanh nghiệp",
  article: "Điều 17",
  clause: "Khoản 2",
  point: "Điểm a",
  source_url: "https://vbpl.vn/example",
};

describe("citationLocation", () => {
  it("ghép Điều, Khoản, Điểm theo thứ tự và bỏ phần null", () => {
    expect(citationLocation(citation)).toBe("Điều 17, Khoản 2, Điểm a");
    expect(citationLocation({ article: "Điều 2", clause: "Khoản 1", point: null })).toBe("Điều 2, Khoản 1");
    expect(citationLocation({ article: "Điều 4", clause: null, point: null })).toBe("Điều 4");
    expect(citedUnitLabel({ clause: null, point: null })).toBe("");
  });
});

describe("locateCitedUnit", () => {
  it("tô cả khoản, dừng trước khoản kế tiếp", () => {
    const text = slice(DIEU_17, "Khoản 2", null)!;
    expect(text.startsWith("2. Tổ chức, cá nhân sau đây")).toBe(true);
    expect(text.endsWith("hạn chế năng lực hành vi dân sự;")).toBe(true);
    expect(text).not.toContain("3. Tổ chức");
  });

  it("tô đúng điểm trong khoản, kể cả điểm đ", () => {
    expect(slice(DIEU_17, "Khoản 2", "Điểm a")).toBe(
      "a) Cơ quan nhà nước, đơn vị lực lượng vũ trang nhân dân sử dụng tài sản nhà nước để thành lập doanh nghiệp;",
    );
    expect(slice(DIEU_17, "Khoản 2", "Điểm đ")).toBe("đ) Người chưa thành niên; người bị hạn chế năng lực hành vi dân sự;");
    expect(slice(DIEU_17, "Khoản 3", "Điểm a")).toBe("a) Cơ quan nhà nước sử dụng tài sản nhà nước góp vốn vào doanh nghiệp để thu lợi riêng;");
  });

  it("tô khoản cuối cùng tới hết Điều", () => {
    expect(slice(DIEU_17, "Khoản 4", null)).toBe(
      "4. Thu lợi riêng cho cơ quan, đơn vị mình quy định tại điểm a khoản 2 và điểm a khoản 3 Điều này là việc sử dụng thu nhập.",
    );
  });

  it("không đoán khi điểm không có khoản và bị trùng giữa các khoản", () => {
    expect(locateCitedUnit(DIEU_17, null, "Điểm a")).toBeNull();
  });

  it("trả null khi không có, nhãn lạ hoặc không trích khoản/điểm", () => {
    expect(locateCitedUnit(DIEU_17, "Khoản 9", null)).toBeNull();
    expect(locateCitedUnit(DIEU_17, "Khoản 2", "Điểm k")).toBeNull();
    expect(locateCitedUnit(DIEU_17, "khoản thứ hai", null)).toBeNull();
    expect(locateCitedUnit(DIEU_17, null, null)).toBeNull();
    expect(locateCitedUnit("Điều này không chia khoản.", "Khoản 1", null)).toBeNull();
  });

  it("không nhầm số trong câu với đầu khoản", () => {
    const content = "1. Theo khoản 2. nêu trên thì áp dụng.\n2. Nội dung khoản hai.";
    expect(slice(content, "Khoản 2", null)).toBe("2. Nội dung khoản hai.");
  });

  it("tìm điểm khi Điều chỉ có điểm, không chia khoản", () => {
    const content = "Doanh nghiệp có các quyền sau:\na) Tự do kinh doanh;\nb) Tự chủ quyết định.";
    expect(slice(content, null, "Điểm b")).toBe("b) Tự chủ quyết định.");
  });
});

describe("answerWithSources", () => {
  it("giữ nguyên câu trả lời và thêm danh sách căn cứ có nguồn", () => {
    const text = answerWithSources("Không được thành lập [C2].", [citation]);
    expect(text).toBe(
      "Không được thành lập [C2].\n\nCăn cứ pháp lý:\n[C2] Điều 17, Khoản 2, Điểm a — Luật Doanh nghiệp. Nguồn: https://vbpl.vn/example",
    );
    expect(answerWithSources("Chưa đủ căn cứ.", [])).toBe("Chưa đủ căn cứ.");
  });
});

describe("documentPageHref", () => {
  it("dùng route Viewer v2.0 và mã hóa tham số", () => {
    expect(documentPageHref(citation)).toBe(
      "/documents/luat-59-2020-qh14-v1?articleId=dieu-17&clause=Kho%E1%BA%A3n+2&point=%C4%90i%E1%BB%83m+a&cite=C2",
    );
    expect(documentPageHref({ ...citation, clause: null, point: null })).toBe("/documents/luat-59-2020-qh14-v1?articleId=dieu-17&cite=C2");
  });
});
