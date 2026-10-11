// Khung hiển thị hội thoại.
import type { Message } from "../../types";
import Icon from "../common/Icon";
import Seal from "../common/Seal";
import MessageBubble from "./MessageBubble";
import { mockSuggestions } from "../../mocks/chatMock";

interface Props {
  messages: Message[];
}

export default function ChatWindow({ messages }: Props) {
  return (
    <div className="chat-scroll">
      {messages.length === 0 ? <Welcome /> : (
        <div className="thread">
          {messages.map((m) => (
            <MessageBubble key={m.id} message={m} />
          ))}
        </div>
      )}
    </div>
  );
}

function Welcome() {
  return (
    <div className="welcome">
      <Seal size={124} withText className="welcome__seal" />
      <h2 className="welcome__title">Bạn cần hỏi gì về luật lao động?</h2>
      <p className="welcome__lead">
        Hỏi về hợp đồng, tiền lương, giờ làm, nghỉ phép hay chấm dứt hợp đồng. Mỗi câu trả lời đều
        kèm điều luật được trích dẫn để bạn đối chiếu.
      </p>
      <ul className="suggestions">
        {mockSuggestions.map((s) => (
          <li key={s.question}>
            <button className="suggestion" type="button">
              <span className="suggestion__field">{s.field}</span>
              <span className="suggestion__q">{s.question}</span>
            </button>
          </li>
        ))}
      </ul>
      <p className="welcome__hint">
        <Icon name="file" size={15} />
        Có thể đính kèm hợp đồng lao động hoặc quyết định kỷ luật để hỏi về nội dung trong đó.
      </p>
    </div>
  );
}
