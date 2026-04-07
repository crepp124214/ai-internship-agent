# tests/unit/business_logic/common/tools/test_web_search.py
import pytest
from unittest.mock import MagicMock

from src.business_logic.common.tools.web_search import WebSearchTool, WebSearchInput


class TestWebSearchTool:
    def setup_method(self):
        self.tool = WebSearchTool()

    def test_returns_error_when_query_empty(self):
        """Test that tool returns error when query is empty."""
        result = self.tool._execute_sync(
            {"query": ""},
            context=MagicMock()
        )

        assert "error" in result
        assert "query is required" in result["error"]

    def test_returns_error_when_query_missing(self):
        """Test that tool returns error when query is not provided."""
        result = self.tool._execute_sync(
            {},
            context=MagicMock()
        )

        assert "error" in result
        assert "query is required" in result["error"]

    def test_returns_search_results_with_default_limit(self):
        """Test that search returns results with default limit of 5."""
        result = self.tool._execute_sync(
            {"query": "Python 开发"},
            context=MagicMock()
        )

        assert "results" in result
        assert result["query"] == "Python 开发"
        assert result["limit"] == 5
        assert len(result["results"]) <= 5

    def test_returns_search_results_with_custom_limit(self):
        """Test that search respects custom limit parameter."""
        result = self.tool._execute_sync(
            {"query": "机器学习", "limit": 3},
            context=MagicMock()
        )

        assert "results" in result
        assert result["limit"] == 3
        assert len(result["results"]) <= 3

    def test_results_have_required_fields(self):
        """Test that each result has title, url, and snippet."""
        result = self.tool._execute_sync(
            {"query": "数据分析"},
            context=MagicMock()
        )

        assert "results" in result
        for item in result["results"]:
            assert "title" in item
            assert "url" in item
            assert "snippet" in item

    def test_results_contain_query_in_title(self):
        """Test that results titles contain the query."""
        query = "前端开发"
        result = self.tool._execute_sync(
            {"query": query},
            context=MagicMock()
        )

        assert "results" in result
        for item in result["results"]:
            assert query in item["title"]

    def test_url_encoding_is_correct(self):
        """Test that query is properly URL encoded in result URLs."""
        query = "Python 机器学习"
        result = self.tool._execute_sync(
            {"query": query},
            context=MagicMock()
        )

        assert "results" in result
        # URL should contain encoded query
        for item in result["results"]:
            assert "q=" in item["url"]

    def test_note_indicates_production_api_needed(self):
        """Test that result includes note about production API."""
        result = self.tool._execute_sync(
            {"query": "测试查询"},
            context=MagicMock()
        )

        assert "note" in result
        assert "SerpAPI" in result["note"]

    def test_limit_of_zero_returns_empty(self):
        """Test that limit of 0 returns no results."""
        result = self.tool._execute_sync(
            {"query": "测试", "limit": 0},
            context=MagicMock()
        )

        assert "results" in result
        assert len(result["results"]) == 0

    def test_input_schema_validation(self):
        """Test that input schema is correctly defined."""
        schema = WebSearchInput
        assert schema.model_fields["query"].is_required()
        assert schema.model_fields["limit"].default == 5

    def test_tool_name_and_description(self):
        """Test that tool has correct name and description."""
        assert self.tool.name == "web_search"
        assert "搜索互联网" in self.tool.description
