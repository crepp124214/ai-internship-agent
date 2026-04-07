# tests/unit/business_logic/jd/test_jd_parser_service.py
import pytest
from src.business_logic.jd.jd_parser_service import JdParserService, ParsedJD


class TestJdParserService:
    def setup_method(self):
        self.service = JdParserService()

    def test_parse_basic_jd(self):
        jd_text = """
        职位：后端开发实习生
        公司：字节跳动

        岗位要求：
        - 熟练掌握 Python/Golang
        - 熟悉 MySQL/Redis
        - 有微服务开发经验优先

        加分项：
        - 了解 Kubernetes
        - 开源社区贡献经历
        """
        result = self.service.parse(jd_text)
        assert isinstance(result, ParsedJD)
        assert result.position == "后端开发实习生"
        assert "Python" in result.required_skills or "Golang" in result.required_skills
        assert len(result.required_skills) >= 2

    def test_parse_extracts_company_from_first_line(self):
        jd_text = "某程旅行 - 前端开发工程师\n\n职位要求：\n- React"
        result = self.service.parse(jd_text)
        assert result.company == "某程旅行"
        assert result.position == "前端开发工程师"

    def test_parse_empty_jd_returns_defaults(self):
        result = self.service.parse("")
        assert result.position == ""
        assert result.required_skills == []
        assert result.qualifications == []
        assert result.highlights == []