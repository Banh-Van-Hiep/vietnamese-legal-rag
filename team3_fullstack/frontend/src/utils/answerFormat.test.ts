import { describe, expect, it } from "vitest";
import { parseAnswer, parseInline } from "./answerFormat";

describe("parseInline", () => {
  it("tách chữ đậm và dấu tham chiếu, giữ nguyên ký tự HTML như văn bản", () => {
    expect(parseInline("Theo **Điều 17** [C1], <b>không</b> [C2]")).toEqual([
      { kind: "text", text: "Theo " },
      { kind: "bold", text: "Điều 17" },
      { kind: "text", text: " " },
      { kind: "cite", citationId: "C1" },
      { kind: "text", text: ", <b>không</b> " },
      { kind: "cite", citationId: "C2" },
    ]);
  });

  it("không coi dấu sao lẻ là chữ đậm", () => {
    expect(parseInline("a * b ** c")).toEqual([{ kind: "text", text: "a * b ** c" }]);
  });
});

describe("parseAnswer", () => {
  it("nhận tiêu đề, đoạn nhiều dòng, gạch đầu dòng và danh sách đánh số", () => {
    const blocks = parseAnswer(
      [
        "Cán bộ, công chức không được thành lập doanh nghiệp [C1].",
        "**Ngoại lệ**",
        "- Được góp vốn trong một số trường hợp [C2]\n- Phải tuân thủ luật chuyên ngành",
        "1. Kiểm tra tư cách\n2. Chuẩn bị hồ sơ",
        "a) Cơ quan nhà nước;\nđ) Người chưa thành niên.",
        "Dòng một\nDòng hai",
      ].join("\n\n"),
    );
    expect(blocks.map((b) => b.kind)).toEqual(["paragraph", "heading", "bullets", "numbered", "numbered", "paragraph"]);
    expect(blocks[1]).toEqual({ kind: "heading", text: "Ngoại lệ" });
    expect(blocks[3]).toMatchObject({ items: [{ marker: "1." }, { marker: "2." }] });
    expect(blocks[4]).toMatchObject({ items: [{ marker: "a)" }, { marker: "đ)" }] });
    expect(blocks[5]).toMatchObject({ lines: [[{ text: "Dòng một" }], [{ text: "Dòng hai" }]] });
  });

  it("đoạn trộn kiểu dòng vẫn là đoạn văn, không tự đánh số", () => {
    expect(parseAnswer("1. Một ý\nvà câu tiếp theo")[0].kind).toBe("paragraph");
    expect(parseAnswer("Dẫn ý:\n1. Một ý\nvà câu tiếp theo")).toHaveLength(1);
  });

  it("tách dòng dẫn khỏi danh sách theo sau", () => {
    const blocks = parseAnswer("Hồ sơ gồm:\n1. Giấy đề nghị [C1]\n2. Điều lệ công ty");
    expect(blocks.map((b) => b.kind)).toEqual(["paragraph", "numbered"]);
    expect(blocks[0]).toMatchObject({ lines: [[{ text: "Hồ sơ gồm:" }]] });
    expect(blocks[1]).toMatchObject({ items: [{ marker: "1.", content: [{ text: "Giấy đề nghị " }, { citationId: "C1" }] }, { marker: "2." }] });
    expect(parseAnswer("- Ý một\n- Ý hai").map((b) => b.kind)).toEqual(["bullets"]);
  });

  it("bỏ qua CRLF và khoảng trắng thừa", () => {
    expect(parseAnswer("  \r\nCâu trả lời.\r\n\r\n\r\nĐoạn hai.\r\n ")).toHaveLength(2);
    expect(parseAnswer("   ")).toEqual([]);
  });
});
