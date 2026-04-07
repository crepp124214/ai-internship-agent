import pytest
from src.data_access.parsers.resume_parser import ResumeParser, ResumeParseResult


class TestResumeParser:
    def test_parse_result_defaults(self):
        result = ResumeParseResult()
        assert result.name is None
        assert result.skills == []
        assert result.raw_text == ""

    def test_extract_skills(self):
        parser = ResumeParser()
        text = "熟悉 Python、Java、Django 和 PostgreSQL"
        result = parser._extract_structured_info(text)

        assert "Python" in result.skills
        assert "Java" in result.skills
        assert "Django" in result.skills
        assert "PostgreSQL" in result.skills

    def test_extract_education(self):
        parser = ResumeParser()
        text = "清华大学 硕士 2020-2023"
        result = parser._extract_structured_info(text)

        assert result.education == "硕士"

    def test_extract_experience(self):
        parser = ResumeParser()
        text = "有 3 年 Python 开发经验"
        result = parser._extract_structured_info(text)

        assert result.experience == "3年"

    def test_unsupported_format(self):
        parser = ResumeParser()
        with pytest.raises(ValueError, match="Unsupported file format"):
            parser.parse(b"content", "resume.txt")