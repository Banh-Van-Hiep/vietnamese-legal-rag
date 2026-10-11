// Trang xem nguyên văn điều luật: /documents/:documentId/articles/:articleId (mở và tải lại được).
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import Icon from "../components/common/Icon";
import DocumentViewer from "../components/document/DocumentViewer";
import Header from "../components/layout/Header";

export default function DocumentPage() {
  const { documentId = "", articleId = "" } = useParams();
  const navigate = useNavigate();
  // location.key là "default" khi trang này là mục đầu tiên của phiên duyệt (mở thẳng bằng link).
  // Tải lại thì trình duyệt giữ lịch sử nên vẫn quay lại được.
  const canGoBack = useLocation().key !== "default";

  return (
    <>
      <Header title="Nguyên văn điều luật" />
      <div className="chat-scroll">
        <div className="page">
          {canGoBack ? (
            <button className="back-link" type="button" onClick={() => navigate(-1)}>
              <Icon name="arrowLeft" size={16} />
              Quay lại
            </button>
          ) : (
            <Link className="back-link" to="/search">
              <Icon name="arrowLeft" size={16} />
              Về trang tra cứu
            </Link>
          )}
          <DocumentViewer documentId={documentId} articleId={articleId} />
        </div>
      </div>
    </>
  );
}
