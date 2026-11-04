"""Unit tests cho Citation Verification Module (Người 2 — Tuần 9, VLRA-67, VLRA-68)."""

import pytest
from team2_rag.prompts.context import BuiltContext, ContextChunk
from team2_rag.verification.metrics import compute_benchmark_metrics
from team2_rag.verification.rubric import SemanticVerdict, evaluate_claim_against_chunk
from team2_rag.verification.types import (
    Claim,
    LLMOutputV2,
    VerificationResult,
)
from team2_rag.verification.verifier import verify_response


@pytest.fixture
def sample_context() -> BuiltContext:
    """Tạo fixture BuiltContext chứa 2 chunk luật mẫu."""
    c1 = ContextChunk(
        label="C1",
        chunk_id="luat-59-2020-qh14-v1__dieu-17__k2__0",
        document_id="luat-59-2020-qh14",
        article_id="dieu-17",
        document_title="Luật Doanh nghiệp 2020",
        article="Điều 17. Quyền thành lập, góp vốn, mua cổ phần, mua phần vốn góp và quản lý doanh nghiệp",
        clause="Khoản 2",
        point=None,
        source_url="https://thuvienphapluat.vn/van-ban/Doanh-nghiep/Luat-Doanh-nghiep-2020-so-59-2020-QH14-432711.aspx",
        content="2. Tổ chức, cá nhân sau đây không có quyền thành lập và quản lý doanh nghiệp tại Việt Nam: a) Cơ quan nhà nước, đơn vị lực lượng vũ trang nhân dân sử dụng tài sản nhà nước để thành lập doanh nghiệp kinh doanh thu lợi riêng cho cơ quan, đơn vị mình; b) Cán bộ, công chức, viên chức theo quy định của pháp luật về cán bộ, công chức, viên chức."
    )
    c2 = ContextChunk(
        label="C2",
        chunk_id="luat-59-2020-qh14-v1__dieu-30__k1__0",
        document_id="luat-59-2020-qh14",
        article_id="dieu-30",
        document_title="Luật Doanh nghiệp 2020",
        article="Điều 30. Đăng ký thay đổi nội dung Giấy chứng nhận đăng ký doanh nghiệp",
        clause="Khoản 1",
        point=None,
        source_url="https://thuvienphapluat.vn/van-ban/Doanh-nghiep/Luat-Doanh-nghiep-2020-so-59-2020-QH14-432711.aspx",
        content="1. Doanh nghiệp phải đăng ký với Cơ quan đăng ký kinh doanh khi thay đổi nội dung Giấy chứng nhận đăng ký doanh nghiệp quy định tại Điều 28 của Luật này trong thời hạn 10 ngày kể từ ngày có thay đổi."
    )
    return BuiltContext(
        text="[C1]...\n\n[C2]...",
        chunks=(c1, c2)
    )


def test_verification_passed_valid_response(sample_context):
    """Test câu trả lời hoàn toàn hợp lệ, trích dẫn đúng và claim được hỗ trợ."""
    output = LLMOutputV2(
        status="answered",
        answer="Cán bộ, công chức không có quyền thành lập và quản lý doanh nghiệp [C1]. Doanh nghiệp phải đăng ký thay đổi trong thời hạn 10 ngày [C2].",
        citations=[
            {
                "citation_id": "C1",
                "chunk_id": "luat-59-2020-qh14-v1__dieu-17__k2__0",
                "document_id": "luat-59-2020-qh14",
                "article_id": "dieu-17",
                "document_title": "Luật Doanh nghiệp 2020",
                "article": "Điều 17. Quyền thành lập, góp vốn, mua cổ phần, mua phần vốn góp và quản lý doanh nghiệp",
                "clause": "Khoản 2",
                "point": None,
                "source_url": "https://thuvienphapluat.vn/van-ban/Doanh-nghiep/Luat-Doanh-nghiep-2020-so-59-2020-QH14-432711.aspx",
            },
            {
                "citation_id": "C2",
                "chunk_id": "luat-59-2020-qh14-v1__dieu-30__k1__0",
                "document_id": "luat-59-2020-qh14",
                "article_id": "dieu-30",
                "document_title": "Luật Doanh nghiệp 2020",
                "article": "Điều 30. Đăng ký thay đổi nội dung Giấy chứng nhận đăng ký doanh nghiệp",
                "clause": "Khoản 1",
                "point": None,
                "source_url": "https://thuvienphapluat.vn/van-ban/Doanh-nghiep/Luat-Doanh-nghiep-2020-so-59-2020-QH14-432711.aspx",
            }
        ],
        claims=[
            Claim(
                claim_id="K1",
                text="Cán bộ, công chức không có quyền thành lập và quản lý doanh nghiệp",
                citation_ids=["C1"]
            ),
            Claim(
                claim_id="K2",
                text="Doanh nghiệp phải đăng ký thay đổi trong thời hạn 10 ngày",
                citation_ids=["C2"]
            )
        ]
    )

    result = verify_response(output, sample_context)

    assert result.passed is True
    assert len(result.claim_results) == 2
    assert result.claim_results[0].supported is True
    assert result.claim_results[1].supported is True
    assert result.summary["hallucination_detected"] is False
    assert result.summary["citation_correctness"] == 1.0
    assert result.summary["citation_coverage"] == 1.0


def test_verification_failed_unsupported_claim(sample_context):
    """Test claim đưa ra thông tin bịa đặt không có trong văn bản luật (Hallucination)."""
    output = LLMOutputV2(
        status="answered",
        answer="Doanh nghiệp phải nộp phạt 500 triệu đồng nếu không đăng ký [C2].",
        citations=[
            {
                "citation_id": "C2",
                "chunk_id": "luat-59-2020-qh14-v1__dieu-30__k1__0",
                "document_id": "luat-59-2020-qh14",
                "article_id": "dieu-30",
                "document_title": "Luật Doanh nghiệp 2020",
                "article": "Điều 30. Đăng ký thay đổi nội dung Giấy chứng nhận đăng ký doanh nghiệp",
                "clause": "Khoản 1",
                "point": None,
                "source_url": "https://thuvienphapluat.vn/van-ban/Doanh-nghiep/Luat-Doanh-nghiep-2020-so-59-2020-QH14-432711.aspx",
            }
        ],
        claims=[
            Claim(
                claim_id="K1",
                text="Doanh nghiệp phải nộp phạt 500 triệu đồng nếu không đăng ký",
                citation_ids=["C2"]
            )
        ]
    )

    result = verify_response(output, sample_context)

    assert result.passed is False
    assert result.claim_results[0].supported is False
    assert result.summary["hallucination_detected"] is True


def test_verification_failed_fake_citation(sample_context):
    """Test citation viện dẫn nhãn lạ không tồn tại trong context (C99)."""
    output = LLMOutputV2(
        status="answered",
        answer="Công chức bị cấm thành lập doanh nghiệp [C99].",
        citations=[
            {
                "citation_id": "C99",
                "chunk_id": "luat-fake-id",
                "document_id": "fake-doc",
                "article_id": "dieu-999",
                "document_title": "Luật Giả",
                "article": "Điều 999",
                "clause": None,
                "point": None,
                "source_url": "https://fake.url",
            }
        ],
        claims=[
            Claim(
                claim_id="K1",
                text="Công chức bị cấm thành lập doanh nghiệp",
                citation_ids=["C99"]
            )
        ]
    )

    result = verify_response(output, sample_context)

    assert result.passed is False
    assert result.citation_results[0].exists_in_context is False
    assert result.summary["all_citations_valid"] is False


def test_verification_failed_metadata_mismatch(sample_context):
    """Test citation trỏ đúng C1 nhưng LLM tự sửa metadata Điều/Khoản thành Điều 99."""
    output = LLMOutputV2(
        status="answered",
        answer="Công chức bị cấm thành lập công ty [C1].",
        citations=[
            {
                "citation_id": "C1",
                "chunk_id": "luat-59-2020-qh14-v1__dieu-17__k2__0",
                "document_id": "luat-59-2020-qh14",
                "article_id": "dieu-99-sai",
                "document_title": "Luật Doanh nghiệp 2020",
                "article": "Điều 99. Tự bịa",
                "clause": None,
                "point": None,
                "source_url": "https://thuvienphapluat.vn/van-ban/Doanh-nghiep/Luat-Doanh-nghiep-2020-so-59-2020-QH14-432711.aspx",
            }
        ],
        claims=[
            Claim(
                claim_id="K1",
                text="Công chức bị cấm thành lập công ty",
                citation_ids=["C1"]
            )
        ]
    )

    result = verify_response(output, sample_context)

    assert result.passed is False
    assert result.citation_results[0].metadata_valid is False


def test_verification_insufficient_context(sample_context):
    """Test trường hợp hệ thống từ chối hợp lệ khi thiếu ngữ cảnh."""
    output = LLMOutputV2(
        status="insufficient_context",
        answer="Tài liệu được truy xuất chưa đủ căn cứ để trả lời.",
        citations=[],
        claims=[]
    )

    result = verify_response(output, sample_context)

    assert result.passed is True
    assert result.summary["status"] == "insufficient_context"
    assert result.summary["hallucination_detected"] is False


def test_benchmark_metrics_computation(sample_context):
    """Test hàm tính toán chỉ số Benchmark đạt mốc cam kết."""
    eval_results = [
        {
            "query_id": "q1",
            "status": "answered",
            "verification_result": VerificationResult(
                passed=True,
                claim_results=[],
                citation_results=[],
                summary={
                    "total_claims": 2,
                    "supported_claims": 2,
                    "total_citations": 2,
                    "valid_citations": 2,
                    "hallucination_detected": False,
                }
            )
        },
        {
            "query_id": "q2",
            "status": "answered",
            "verification_result": VerificationResult(
                passed=False,
                claim_results=[],
                citation_results=[],
                summary={
                    "total_claims": 1,
                    "supported_claims": 0,
                    "total_citations": 1,
                    "valid_citations": 0,
                    "hallucination_detected": True,
                }
            )
        },
        {
            "query_id": "q3",
            "status": "insufficient_context",
            "verification_result": VerificationResult(
                passed=True,
                claim_results=[],
                citation_results=[],
                summary={"status": "insufficient_context"}
            )
        }
    ]

    metrics = compute_benchmark_metrics(eval_results)

    assert metrics["dataset_summary"]["total_queries"] == 3
    assert metrics["dataset_summary"]["answered_queries"] == 2
    assert metrics["dataset_summary"]["insufficient_context_queries"] == 1

    # Citation correctness: 2 / 3 = 0.6667
    assert metrics["core_metrics"]["citation_correctness"] == 0.6667
    # Citation coverage: 2 / 3 = 0.6667
    assert metrics["core_metrics"]["citation_coverage"] == 0.6667
    # Hallucination rate: 1 / 2 = 0.50
    assert metrics["core_metrics"]["hallucination_rate"] == 0.50
