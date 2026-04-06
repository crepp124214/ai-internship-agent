import pytest
from src.business_logic.jd.schemas import ParsedJD, MatchReport
from src.business_logic.jd.resume_match_service import ResumeMatchService


class TestResumeMatchService:
    def setup_method(self):
        self.service = ResumeMatchService()

    def test_compute_match_basic(self):
        jd = ParsedJD(
            company="ByteDance",
            position="Backend Engineer",
            required_skills=["Python", "MySQL", "Redis"],
            qualifications=["3+ years experience", "Bachelor's degree"],
            highlights=["Stock options", "Flexible hours"],
            raw_text="...",
        )
        resume_text = "I have 4 years of experience with Python, MySQL, and built Redis caching systems."
        report = self.service.compute_match(resume_text, jd)
        assert isinstance(report, MatchReport)
        assert report.match_score > 0.5
        assert report.keyword_coverage["Python"] is True
        assert report.keyword_coverage["MySQL"] is True

    def test_compute_match_all_keywords_found(self):
        jd = ParsedJD(
            company=None, position="DevOps",
            required_skills=["Docker", "Kubernetes"],
            qualifications=[], highlights=[], raw_text="..."
        )
        resume_text = "Experienced with Docker and Kubernetes deployments."
        report = self.service.compute_match(resume_text, jd)
        assert report.keyword_coverage["Docker"] is True
        assert report.keyword_coverage["Kubernetes"] is True
        assert report.match_score == 1.0

    def test_compute_match_no_keywords_found(self):
        jd = ParsedJD(
            company=None, position="Chef",
            required_skills=["Cooking", "Knives"],
            qualifications=[], highlights=[], raw_text="..."
        )
        resume_text = "I write Python code and love databases."
        report = self.service.compute_match(resume_text, jd)
        assert report.match_score == 0.0
        assert report.keyword_coverage["Cooking"] is False
        assert len(report.gaps) == 2

    def test_suggestions_generated_when_gaps_exist(self):
        jd = ParsedJD(
            company=None, position="ML Engineer",
            required_skills=["TensorFlow", "PyTorch"],
            qualifications=[], highlights=["Cutting-edge research"], raw_text="..."
        )
        resume_text = "I use basic Python scripting."
        report = self.service.compute_match(resume_text, jd)
        assert len(report.suggestions) > 0
        assert len(report.gaps) == 2
