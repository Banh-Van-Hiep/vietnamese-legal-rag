"""Lỗi retrieval, theo docs/team1_data/retrieval-design.md mục 4.2."""


class RetrievalUnavailableError(RuntimeError):
    """Index không nạp được hoặc không khớp với chunk store."""
