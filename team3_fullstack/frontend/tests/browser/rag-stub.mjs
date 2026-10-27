/** TEST ONLY: HTTP fixtures for FE -> real Java -> internal JSON integration.
 * This is not Team2's service, a retrieval implementation, or a live RAG demo. */
import { createServer } from "node:http";
const port = Number(process.env.STUB_PORT ?? 18042);
const calls = [];
const counts = new Map();
const citation = { citation_id: "C1", chunk_id: "mock_v1_art1_k1", document_id: "mock_v1",
  article_id: "art1", document_title: "Văn bản kiểm thử", article: "Điều 1", clause: null,
  point: null, source_url: "https://example.com/mock-law" };
const send = (res, status, body) => { res.writeHead(status, { "Content-Type": "application/json; charset=utf-8" }); res.end(JSON.stringify(body)); };
const server = createServer(async (req, res) => {
  const url = new URL(req.url, `http://127.0.0.1:${port}`);
  if (url.pathname === "/__test/state") { send(res, 200, { calls }); return; }
  if (req.method === "POST" && url.pathname === "/internal/v1/query") {
    let input;
    try { let raw = ""; for await (const part of req) raw += part; input = JSON.parse(raw); }
    catch { send(res,400,{error:{code:"INVALID_REQUEST",message:"Bad test input",retryable:false}}); return; }
    const keys=Object.keys(input).sort().join(",");
    if(keys!=="history,question" || !Array.isArray(input.history) || typeof input.question!=="string") {
      send(res,400,{error:{code:"INVALID_REQUEST",message:"Bad test contract",retryable:false}}); return;
    }
    const q = input.question;
    counts.set(q, (counts.get(q) ?? 0) + 1);
    calls.push({ question: q, history: input.history, trace: req.headers["x-request-id"] });
    if (/Slow|Reload pending|Switch pending/.test(q)) await new Promise((r) => setTimeout(r, 1800));
    if (q.startsWith("Known failure") && counts.get(q) === 1) {
      send(res,503,{error:{code:"LLM_UNAVAILABLE",message:"Dịch vụ kiểm thử tạm thời không sẵn sàng.",retryable:true}}); return;
    }
    if (q.startsWith("Insufficient")) { send(res,200,{status:"insufficient_context",answer:"Dữ liệu thử nghiệm chưa đủ căn cứ.",citations:[]}); return; }
    const c={...citation,...(q.startsWith("Missing source")?{article_id:"missing"}: {})};
    send(res,200,{status:"answered",answer:`Dữ liệu giả lập kiểm thử cho ${q} [C1].`,citations:[c]}); return;
  }
  const article = url.pathname.match(/^\/internal\/v1\/documents\/([^/]+)\/articles\/([^/]+)$/);
  if (req.method === "GET" && article) {
    if (article[1] !== "mock_v1" || article[2] === "missing") {
      send(res,404,{error:{code:"ARTICLE_NOT_FOUND",message:"Không tìm thấy nguồn kiểm thử.",retryable:false}}); return;
    }
    send(res,200,{document_id:"mock_v1",article_id:article[2],document_title:"Văn bản kiểm thử",article:"Điều 1",
      content:"Nguyên văn đầy đủ chỉ dùng để kiểm thử FE–BE. Đây không phải quy định pháp luật thật.",source_url:"https://example.com/mock-law"}); return;
  }
  send(res,404,{error:{code:"NOT_FOUND",message:"Unknown fixture path",retryable:false}});
});
server.listen(port,"127.0.0.1",()=>console.log(`TEST FIXTURE ONLY listening on http://127.0.0.1:${port}`));
