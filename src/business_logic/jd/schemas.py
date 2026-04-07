from typing import NamedTuple


class ParsedJD(NamedTuple):
    """Parsed Job Description"""
    company: str | None
    position: str
    required_skills: list[str]
    qualifications: list[str]
    highlights: list[str]
    raw_text: str


class MatchReport(NamedTuple):
    """Resume-JD Match Report"""
    keyword_coverage: dict[str, bool]
    match_score: float
    gaps: list[str]
    suggestions: list[str]
