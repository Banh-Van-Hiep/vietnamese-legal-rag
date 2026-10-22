// Trang xem nguyên văn điều luật: /documents/:documentId/articles/:articleId (mở và tải lại được).
import { Link, useLocation, useNavigate, useParams, useSearchParams } from "react-router-dom";
import Icon from "../components/common/Icon";
import DocumentViewer from "../components/document/DocumentViewer";
import Header from "../components/layout/Header";

const backLinkClass = "mb-[18px] inline-flex items-center gap-1.5 py-1 pr-2 text-[14px] text-muted hover:text-ink";

export default function DocumentPage() {
  const { documentId = "", articleId: legacyArticleId = "" } = useParams();
  const [parameters] = useSearchParams();
  const articleId = parameters.get("articleId") ?? legacyArticleId;
  const navigate = useNavigate();
  // location.key là "default" khi trang này là mục đầu tiên của phiên duyệt (mở thẳng bằng link).
  // Tải lại thì trình duyệt giữ lịch sử nên vẫn quay lại được.
  const canGoBack = useLocation().key !== "default";

  return (
    <>
      <Header title="Nguyên văn điều luật" />
      <div className="flex-1 overflow-y-auto px-6 max-[600px]:px-4">
        <div className="mx-auto max-w-[760px] pt-7 pb-10">
          {canGoBack ? (
            <button className={backLinkClass} type="button" data-testid="back-link" onClick={() => navigate(-1)}>
              <Icon name="arrowLeft" size={16} />
              Quay lại
            </button>
          ) : (
            <Link className={backLinkClass} to="/search" data-testid="back-link">
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
