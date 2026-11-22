import { describe, expect, it } from "vitest";
import { parseMockMode } from "./MockBadge";

// Main UI dùng dữ liệu thật: nhãn "Dữ liệu thử nghiệm" chỉ hiện khi bật rõ VITE_MOCK_MODE=true.
describe("parseMockMode", () => {
  it.each([["true"], ["TRUE"], [" true "]])("%j bật nhãn", (value) => {
    expect(parseMockMode(value)).toBe(true);
  });
  it.each([[undefined], [""], ["false"], ["1"], ["yes"]])("%j không bật nhãn", (value) => {
    expect(parseMockMode(value)).toBe(false);
  });
});
