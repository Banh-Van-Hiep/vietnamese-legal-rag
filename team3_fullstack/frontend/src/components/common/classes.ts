// Chuỗi class Tailwind dùng ở nhiều nơi, để các thẻ cùng loại luôn giống nhau.

/** Thẻ căn cứ pháp lý / kết quả tra cứu: nền giấy, viền trái đỏ con dấu. */
export const cardClass =
  "rounded-sm border border-l-[3px] border-line border-l-seal bg-paper px-[18px] pt-4 pb-3";

/** Liên kết "Xem nguyên văn điều luật". */
export const openLinkClass =
  "inline-block py-1 text-[13px] font-medium text-seal-strong underline-offset-[3px] hover:underline";

/** Dòng trạng thái ở giữa vùng nội dung: đang tải, chưa có kết quả. */
export const statusTextClass = "mx-auto mt-[12vh] text-center text-muted";
