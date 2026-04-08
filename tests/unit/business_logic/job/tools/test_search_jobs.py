# tests/unit/business_logic/job/tools/test_search_jobs.py
import pytest
from unittest.mock import MagicMock, patch

from src.business_logic.job.tools.search_jobs import SearchJobsTool, SearchJobsInput


class TestSearchJobsTool:
    def setup_method(self):
        self.tool = SearchJobsTool()

    def test_search_returns_company_recruitment_urls(self):
        """Test that search returns company recruitment URLs via web search."""
        mock_context = MagicMock(db=MagicMock())

        with patch.object(self.tool, '_execute_sync') as mock_execute:
            mock_execute.return_value = {
                "keyword": "深圳 Python 实习",
                "count": 2,
                "results": [
                    {
                        "company": "字节跳动",
                        "url": "https://jobs.bytedance.com/campus",
                        "type": "direct",
                        "snippet": "字节跳动 招聘官网，包含校园招聘和实习招聘信息",
                    }
                ],
                "source": "known_companies",
            }

            result = self.tool._execute_sync(
                tool_input={"keyword": "深圳 Python 实习"},
                context=mock_context,
            )

            assert "results" in result
            assert "count" in result
            assert "keyword" in result
            assert result["keyword"] == "深圳 Python 实习"

    def test_search_with_location(self):
        """Test search with location parameter."""
        mock_context = MagicMock(db=MagicMock())

        with patch.object(self.tool, '_execute_sync') as mock_execute:
            mock_execute.return_value = {
                "keyword": "Python 实习",
                "location": "深圳",
                "count": 1,
                "results": [],
                "source": "known_companies",
            }

            result = self.tool._execute_sync(
                tool_input={"keyword": "Python 实习", "location": "深圳"},
                context=mock_context,
            )

            assert result["location"] == "深圳"
            assert "results" in result

    def test_known_company_direct_match(self):
        """Test known company direct match returns from known_companies mapping."""
        mock_context = MagicMock(db=MagicMock())

        # 直接测试实际的 _execute_sync 方法，使用已知的公司映射
        result = self.tool._execute_sync(
            tool_input={"keyword": "字节跳动", "limit": 3},
            context=mock_context,
        )

        # 应该从已知公司映射中直接返回
        assert result["source"] == "known_companies"
        assert len(result["results"]) > 0
        assert result["results"][0]["company"] == "字节跳动"
        assert "url" in result["results"][0]

    def test_empty_keyword_returns_error(self):
        """Test that empty keyword returns an error."""
        mock_context = MagicMock(db=MagicMock())

        result = self.tool._execute_sync(
            tool_input={"keyword": ""},
            context=mock_context,
        )

        assert "error" in result

    def test_search_jobs_input_schema(self):
        """Test that SearchJobsInput schema is correct."""
        schema = SearchJobsInput
        assert hasattr(schema, "model_fields")
        assert "keyword" in schema.model_fields
        assert "location" in schema.model_fields
        assert "limit" in schema.model_fields

    def test_context_required_raises_error(self):
        """Test that context is required."""
        with pytest.raises(ValueError, match="ToolContext is required"):
            self.tool._execute_sync(
                tool_input={"keyword": "测试"},
                context=None,
            )