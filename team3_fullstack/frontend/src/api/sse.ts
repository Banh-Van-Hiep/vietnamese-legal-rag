/** Incremental SSE framing; UTF-8 decoding belongs to the byte-stream caller. */
export class SseParser {
  private buffer = "";
  private event = "";
  private data: string[] = [];
  private size = 0;
  constructor(private readonly emit: (event: string, data: unknown) => void) { }
  push(chunk: string) {
    this.buffer += chunk;
    if (this.buffer.length + this.size > 512 * 1024) throw new Error("SSE frame too large");
    let newline: number;
    while ((newline = this.buffer.indexOf("\n")) >= 0) {
      const line = this.buffer.slice(0, newline).replace(/\r$/, "");
      this.buffer = this.buffer.slice(newline + 1);
      if (!line) {
        if (this.data.length) this.emit(this.event || "message", JSON.parse(this.data.join("\n")));
        this.event = ""; this.data = []; this.size = 0;
      } else if (!line.startsWith(":")) {
        const colon = line.indexOf(":");
        const field = colon < 0 ? line : line.slice(0, colon);
        let value = colon < 0 ? "" : line.slice(colon + 1);
        if (value.startsWith(" ")) value = value.slice(1);
        if (field === "event") this.event = value;
        if (field === "data") { this.data.push(value); this.size += value.length; }
      }
    }
  }
}
