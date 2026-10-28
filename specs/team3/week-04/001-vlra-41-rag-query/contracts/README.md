# Contract references — VLRA-41

Căn cứ [Docs v2.0](https://docs.google.com/document/d/1uDCSGNfzWXIaCSdggRrxcSuRREJ3StS278r4vZWNYPM/edit?tab=t.0) §9.1–9.10, §9.13–9.16.

POST /api/v1/chat/stream: JSON question, clientRequestId, optional/null conversationId;
Accept text/event-stream; no extra/query fields, duplicate keys or coercion.
SSE meta → optional heartbeat → delta (answered only, 0..N) → complete; or error terminal.
Complete eight camelCase fields, public citation nine fields; numeric safe IDs.
Internal POST /internal/v1/query: question/history only, X-Request-ID UUID; RagResponse
status/answer/citations snake_case. Required keys include nullable clause/point.
HTTP error logical mapping per §9.14, never expose upstream raw message.
Conversation arrays/read/delete support recovery; no Viewer changes in VLRA-41.
Shared contracts/v0.1/query_request schema remains legacy, not SSE validator.

Schema public tại [chat-v2.schema.json](chat-v2.schema.json), draft2020-12; event name chọn $defs tương ứng. Marker/provenance/history/state cần semantic tests bên cạnh schema. Không sửa shared contracts/v0.1.
