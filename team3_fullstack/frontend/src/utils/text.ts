/** Số ký tự theo Unicode code point, cùng cách backend đếm (giới hạn câu hỏi 2000). */
export const codePointLength = (text: string) => Array.from(text).length;

/** Cắt theo code point để không tách đôi ký tự. */
export const truncate = (text: string, max: number) => Array.from(text).slice(0, max).join("");

/** Chuẩn hóa để so khớp từ khóa: bỏ dấu tiếng Việt, đưa về chữ thường. */
export const normalize = (text: string) =>
  text
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/đ/g, "d")
    .replace(/Đ/g, "D")
    .toLowerCase();
