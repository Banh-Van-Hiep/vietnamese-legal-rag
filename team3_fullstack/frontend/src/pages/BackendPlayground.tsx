import { useEffect, useRef, useState, type FormEvent } from "react";
import { BASE_URL } from "../api/client";
import {
  askBackend, checkBackendHealth, openBackendArticle, PlaygroundApiError,
  type PlaygroundAnswer, type PlaygroundArticle, type PlaygroundCitation,
} from "../api/backendPlaygroundApi";
import "../styles/backend-playground.css";

type Turn = { id: string; question: string; response?: PlaygroundAnswer; error?: string };
const samples = ["Điều kiện để hợp đồng có hiệu lực là gì?", "Tôi muốn xem nội dung điều luật được trích dẫn."];

function errorMessage(error: unknown): string {
  if (error instanceof PlaygroundApiError) return `${error.message} (HTTP ${error.status})`;
  return "Không kết nối được Backend. Kiểm tra server và thử lại.";
}

export default function BackendPlayground() {
  const [question, setQuestion] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [health, setHealth] = useState<"checking" | "up" | "down">("checking");
  const [validation, setValidation] = useState("");
  const [article, setArticle] = useState<PlaygroundArticle | null>(null);
  const [articleError, setArticleError] = useState("");
  const [articleLoading, setArticleLoading] = useState(false);
  const [viewerOpen, setViewerOpen] = useState(false);
  const articleRequest = useRef<AbortController | null>(null);
  const bottom = useRef<HTMLDivElement | null>(null);
  const input = useRef<HTMLTextAreaElement | null>(null);
  const trimmed = question.trim();
  const count = Array.from(trimmed).length;

  useEffect(() => {
    const controller = new AbortController();
    checkBackendHealth(controller.signal)
      .then((result) => setHealth(result.status === "up" ? "up" : "down"))
      .catch(() => { if (!controller.signal.aborted) setHealth("down"); });
    return () => { controller.abort(); articleRequest.current?.abort(); };
  }, []);

  useEffect(() => { bottom.current?.scrollIntoView({ behavior: "smooth", block: "end" }); }, [turns]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (sending) return;
    if (count < 1 || count > 2000) {
      setValidation("Câu hỏi cần từ 1 đến 2.000 ký tự.");
      return;
    }
    const id = crypto.randomUUID();
    setValidation("");
    setSending(true);
    setQuestion("");
    setTurns((current) => [...current, { id, question: trimmed }]);
    try {
      const response = await askBackend(trimmed, conversationId);
      setConversationId(response.conversation_id);
      setHealth("up");
      setTurns((current) => current.map((turn) => turn.id === id ? { ...turn, response } : turn));
    } catch (error) {
      if (error instanceof PlaygroundApiError && error.conversationId) setConversationId(error.conversationId);
      if (!(error instanceof PlaygroundApiError)) setHealth("down");
      setTurns((current) => current.map((turn) => turn.id === id ? { ...turn, error: errorMessage(error) } : turn));
    } finally { setSending(false); input.current?.focus(); }
  }

  function newConversation() {
    if (sending) return;
    articleRequest.current?.abort();
    setTurns([]);
    setConversationId(null);
    setQuestion("");
    setValidation("");
    setViewerOpen(false);
    setArticle(null);
    setArticleError("");
    setArticleLoading(false);
    input.current?.focus();
  }

  async function openSource(citation: PlaygroundCitation) {
    articleRequest.current?.abort();
    const controller = new AbortController();
    articleRequest.current = controller;
    setViewerOpen(true);
    setArticle(null);
    setArticleError("");
    setArticleLoading(true);
    try { setArticle(await openBackendArticle(citation, controller.signal)); }
    catch (error) { if (!controller.signal.aborted) setArticleError(errorMessage(error)); }
    finally { if (!controller.signal.aborted) setArticleLoading(false); }
  }

  return (
    <div className="backend-playground">
      <header className="playground-header">
        <a className="playground-brand" href="/try-backend" aria-label="Trang thử Backend">
          <span className="playground-logo" aria-hidden="true">§</span>
          <span>Legal RAG <small>Team 3 · Local playground</small></span>
        </a>
        <div className="playground-connection" role="status">
          <span className={`playground-dot ${health}`} />
          {health === "up" ? "Backend đang chạy" : health === "checking" ? "Đang kết nối…" : "Chưa kết nối"}
        </div>
      </header>

      <main className="playground-main">
        <aside className="playground-sidebar">
          <span className="playground-eyebrow">THỬ BACKEND T02</span>
          <h1>Hỏi đáp<br />{" "}và xem nguồn.</h1>
          <p>Gửi câu hỏi tới Backend và mở điều luật mẫu từ trích dẫn.</p>
          <button className="playground-new" onClick={newConversation} disabled={sending}>＋ Hội thoại mới</button>
          <div className="playground-note">
            <strong>Đang dùng dữ liệu mock</strong>
            <p>Câu trả lời là mẫu kiểm tra API, chưa phân tích câu hỏi bằng RAG và không phải tư vấn pháp lý.</p>
          </div>
          <div className="playground-meta">
            <span>Backend</span><code>{BASE_URL}</code>
            <span>Hội thoại hiện tại</span>
            <code>{conversationId ?? "Chưa tạo · gửi câu hỏi đầu tiên"}</code>
            <p>Hỏi tiếp giữ cùng hội thoại. “Hội thoại mới” bắt đầu một cuộc trò chuyện khác.</p>
          </div>
        </aside>

        <section className="playground-chat" aria-label="Hỏi thử Backend">
          <div className="playground-chat-title"><h2>Cuộc trò chuyện</h2><span>Mock API</span></div>
          <div className="playground-messages" aria-live="polite" aria-busy={sending}>
            {turns.length === 0 && (
              <div className="playground-empty">
                <span className="playground-empty-icon" aria-hidden="true">§</span>
                <h2>Bắt đầu bằng một câu hỏi</h2>
                <p>Thử gửi tiếng Việt, nhận câu trả lời và nhấn trích dẫn để xem nguồn.</p>
                <div className="playground-samples">
                  {samples.map((sample) => <button key={sample} onClick={() => { setQuestion(sample); input.current?.focus(); }}>{sample}<span aria-hidden="true">↗</span></button>)}
                </div>
              </div>
            )}
            {turns.map((turn) => (
              <div className="playground-turn" key={turn.id}>
                <div className="playground-user"><span>BẠN</span><p>{turn.question}</p></div>
                <div className={`playground-assistant${turn.error ? " has-error" : ""}`}>
                  <span>LEGAL RAG <small>{turn.response?.status === "insufficient_context" ? "Thiếu căn cứ" : "Mock"}</small></span>
                  {turn.error ? <p role="alert">{turn.error}</p> : turn.response ? (
                    <>
                      <p>{turn.response.answer}</p>
                      {turn.response.citations.length > 0 && <div className="playground-citations">
                        {turn.response.citations.map((citation) => (
                          <button key={citation.citation_id} onClick={() => openSource(citation)}>
                            <b>[{citation.citation_id}]</b><span>{citation.document_title}<small>{[citation.article, citation.clause, citation.point].filter(Boolean).join(" · ")}</small></span><span aria-hidden="true">↗</span>
                          </button>
                        ))}
                      </div>}
                    </>
                  ) : <p className="playground-pending" role="status">Đang chờ Backend…</p>}
                </div>
              </div>
            ))}
            <div ref={bottom} />
          </div>
          <form className="playground-composer" onSubmit={submit}>
            <label htmlFor="playground-question">Câu hỏi của bạn</label>
            <div className="playground-input-row">
              <textarea id="playground-question" ref={input} rows={2} value={question} placeholder="Nhập câu hỏi bằng tiếng Việt…" disabled={sending}
                aria-describedby="playground-input-help" onChange={(event) => { setQuestion(event.target.value); setValidation(""); }}
                onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) { event.preventDefault(); event.currentTarget.form?.requestSubmit(); } }} />
              <button type="submit" disabled={sending || count < 1 || count > 2000}>{sending ? "Đang gửi…" : "Gửi câu hỏi"}<span aria-hidden="true"> ↑</span></button>
            </div>
            <div className="playground-input-help" id="playground-input-help"><span>Enter để gửi · Shift + Enter để xuống dòng</span><span className={count > 2000 ? "over-limit" : ""}>{count.toLocaleString("vi-VN")} / 2.000</span></div>
            {validation && <p className="playground-validation" role="alert">{validation}</p>}
          </form>
        </section>

        {viewerOpen && <aside className="playground-viewer" aria-label="Nội dung nguồn trích dẫn">
          <div className="playground-viewer-top"><span className="playground-eyebrow">NGUỒN TRÍCH DẪN</span><button aria-label="Đóng nguồn" onClick={() => { articleRequest.current?.abort(); setViewerOpen(false); }}>×</button></div>
          {articleLoading && <p role="status">Đang tải điều luật…</p>}
          {articleError && <p className="playground-validation" role="alert">{articleError}</p>}
          {article && <>
            <h2>{article.document_title}</h2><h3>{article.article}</h3>
            <p className="playground-source-content">{article.content}</p>
            {article.source_url.startsWith("https://") && <a className="playground-source-link" href={article.source_url} target="_blank" rel="noopener noreferrer">Mở URL nguồn ↗</a>}
            <p className="playground-source-note">Văn bản mẫu kiểm tra cấu trúc, chưa phải nguồn luật thật.</p>
          </>}
        </aside>}
      </main>
    </div>
  );
}
