# tests/unit/business_logic/common/tools/test_extract_keywords.py
import pytest
from unittest.mock import MagicMock

from src.business_logic.common.tools.extract_keywords import (
    ExtractKeywordsTool,
    ExtractKeywordsInput,
)


class TestExtractKeywordsTool:
    def setup_method(self):
        self.tool = ExtractKeywordsTool()

    def test_returns_error_when_text_empty(self):
        """Test that tool returns error when text is empty."""
        result = self.tool._execute_sync(
            {"text": ""},
            context=MagicMock()
        )
        assert "error" in result
        assert "text is required" in result["error"]

    def test_extracts_keywords_from_simple_text(self):
        """Test basic keyword extraction."""
        result = self.tool._execute_sync(
            {"text": "Python 编程 Python 开发 Django 框架"},
            context=MagicMock()
        )
        assert "keywords" in result
        assert result["keyword_count"] > 0

    def test_python_keyword_count(self):
        """Test that Python appears with correct count."""
        result = self.tool._execute_sync(
            {"text": "Python 编程 Python 开发 Python 应用"},
            context=MagicMock()
        )
        python_entries = [k for k in result["keywords"] if k["word"] == "python"]
        assert len(python_entries) == 1
        assert python_entries[0]["count"] == 3

    def test_stop_words_filtered(self):
        """Test that stop words are filtered out."""
        result = self.tool._execute_sync(
            {"text": "这是 一个 测试 文本"},
            context=MagicMock()
        )
        words = [k["word"] for k in result["keywords"]]
        assert "这" not in words
        assert "是" not in words
        assert "一个" not in words

    def test_english_stop_words_filtered(self):
        """Test that English stop words are filtered out."""
        result = self.tool._execute_sync(
            {"text": "the a is are was were be been testing python development"},
            context=MagicMock()
        )
        words = [k["word"] for k in result["keywords"]]
        assert "the" not in words
        assert "a" not in words
        assert "is" not in words
        assert "are" not in words
        assert "was" not in words
        assert "were" not in words
        assert "be" not in words
        assert "been" not in words

    def test_short_words_filtered(self):
        """Test that words with length <= 2 are filtered out."""
        result = self.tool._execute_sync(
            {"text": "我 在 北京 工作"},
            context=MagicMock()
        )
        words = [k["word"] for k in result["keywords"]]
        assert "在" not in words
        assert "北京" in words or "工作" in words

    def test_limit_parameter(self):
        """Test that limit parameter controls number of keywords."""
        result = self.tool._execute_sync(
            {"text": "Python Python Python Java Java Java Java Java Java Java Go Go Go Go Go", "limit": 3},
            context=MagicMock()
        )
        assert result["keyword_count"] <= 3

    def test_default_limit_is_10(self):
        """Test that default limit is 10."""
        tool = ExtractKeywordsTool()
        schema = ExtractKeywordsInput
        assert schema.model_fields["limit"].default == 10

    def test_text_length_returned(self):
        """Test that text_length is returned in result."""
        result = self.tool._execute_sync(
            {"text": "Python 编程"},
            context=MagicMock()
        )
        assert "text_length" in result
        assert result["text_length"] == len("Python 编程")

    def test_keywords_sorted_by_frequency(self):
        """Test that keywords are sorted by frequency descending."""
        result = self.tool._execute_sync(
            {"text": "苹果 香蕉 苹果 香蕉 香蕉 香蕉"},
            context=MagicMock()
        )
        assert result["keywords"][0]["word"] == "香蕉"
        assert result["keywords"][0]["count"] == 4
        assert result["keywords"][1]["word"] == "苹果"
        assert result["keywords"][1]["count"] == 2

    def test_case_insensitive(self):
        """Test that extraction is case insensitive."""
        result = self.tool._execute_sync(
            {"text": "Python PYTHON python"},
            context=MagicMock()
        )
        assert result["keyword_count"] == 1
        assert result["keywords"][0]["count"] == 3

    def test_input_schema_validation(self):
        """Test that input schema is correctly defined."""
        schema = ExtractKeywordsInput
        assert schema.model_fields["text"].is_required()
        assert schema.model_fields["limit"].default == 10

    def test_empty_result_for_only_stop_words(self):
        """Test that empty keywords for text with only stop words."""
        result = self.tool._execute_sync(
            {"text": "的 了 是 在"},
            context=MagicMock()
        )
        assert result["keyword_count"] == 0

    def test_resume_jd_analysis_use_case(self):
        """Test with typical JD/resume text."""
        text = "熟悉 Python 编程语言，了解 Django 和 Flask 框架，有数据库设计和 SQL 优化经验，熟悉微服务架构和 Docker 容器化部署"
        result = self.tool._execute_sync(
            {"text": text, "limit": 10},
            context=MagicMock()
        )
        assert "python" in [k["word"] for k in result["keywords"]]
        assert "django" in [k["word"] for k in result["keywords"]] or "flask" in [k["word"] for k in result["keywords"]]

    def test_keyword_structure(self):
        """Test that each keyword has correct structure."""
        result = self.tool._execute_sync(
            {"text": "Python 编程"},
            context=MagicMock()
        )
        for kw in result["keywords"]:
            assert "word" in kw
            assert "count" in kw
            assert isinstance(kw["word"], str)
            assert isinstance(kw["count"], int)