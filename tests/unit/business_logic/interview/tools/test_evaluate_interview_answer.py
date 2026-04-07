# tests/unit/business_logic/interview/tools/test_evaluate_interview_answer.py
import pytest
from unittest.mock import MagicMock

from src.business_logic.interview.tools.evaluate_interview_answer import (
    EvaluateInterviewAnswerTool,
    EvaluateInterviewAnswerInput,
)


class TestEvaluateInterviewAnswerTool:
    def setup_method(self):
        self.tool = EvaluateInterviewAnswerTool()

    def test_returns_error_when_question_empty(self):
        """Test that tool returns error when question is empty."""
        result = self.tool._execute_sync(
            {"question": "", "answer": "some answer"},
            context=MagicMock()
        )
        assert "error" in result
        assert "question and answer are required" in result["error"]

    def test_returns_error_when_answer_empty(self):
        """Test that tool returns error when answer is empty."""
        result = self.tool._execute_sync(
            {"question": "some question", "answer": ""},
            context=MagicMock()
        )
        assert "error" in result
        assert "question and answer are required" in result["error"]

    def test_short_answer_penalty(self):
        """Test that short answers get lower scores."""
        result = self.tool._execute_sync(
            {"question": "介绍一下你自己", "answer": "我是开发者"},
            context=MagicMock()
        )
        assert result["score"] == 2
        assert "过于简短" in result["suggestions"][0]

    def test_long_answer_bonus(self):
        """Test that longer answers get bonus points."""
        result = self.tool._execute_sync(
            {"question": "介绍一下你自己", "answer": "我是一名有着五年经验的全栈工程师，负责过多个大型项目的架构设计和技术团队管理。"},
            context=MagicMock()
        )
        assert result["score"] >= 3

    def test_star_keywords_bonus(self):
        """Test that STAR keywords add bonus points."""
        result = self.tool._execute_sync(
            {"question": "描述一个项目经验", "answer": "我负责实现了一个电商系统，使用微服务架构完成了订单和支付模块的开发，项目上线后性能提升了50%。"},
            context=MagicMock()
        )
        assert result["score"] >= 3

    def test_star_suggestion_when_no_star_keywords(self):
        """Test that STAR suggestion is given when no STAR keywords found."""
        result = self.tool._execute_sync(
            {"question": "描述一个项目经验", "answer": "我做了一个网站。"},
            context=MagicMock()
        )
        suggestions_text = " ".join(result["suggestions"])
        assert "STAR" in suggestions_text

    def test_technical_category_keywords(self):
        """Test that technical category checks for technical keywords."""
        result = self.tool._execute_sync(
            {"question": "如何优化系统性能", "answer": "我通过架构优化和性能调优，使用缓存和异步处理提升了系统吞吐量。", "category": "技术"},
            context=MagicMock()
        )
        assert result["score"] >= 4

    def test_rating_excellent(self):
        """Test excellent rating for high scores."""
        result = self.tool._execute_sync(
            {"question": "描述项目经验", "answer": "我负责实现电商系统，使用微服务架构完成订单和支付模块的开发，通过架构优化和性能调优使系统吞吐量提升了50%，项目成功上线并稳定运行。"},
            context=MagicMock()
        )
        assert result["rating"] == "优秀"
        assert result["score"] >= 8

    def test_rating_good(self):
        """Test good rating for moderate scores."""
        result = self.tool._execute_sync(
            {"question": "描述项目经验", "answer": "我负责开发了一个项目，使用Django框架设计了系统架构。"},
            context=MagicMock()
        )
        assert result["rating"] == "良好"
        assert 6 <= result["score"] <= 10

    def test_rating_average(self):
        """Test average rating for low scores."""
        result = self.tool._execute_sync(
            {"question": "描述项目经验", "answer": "我做了一个项目。"},
            context=MagicMock()
        )
        assert result["rating"] == "一般"
        assert 4 <= result["score"] < 6

    def test_rating_need_improvement(self):
        """Test need improvement rating for very low scores."""
        result = self.tool._execute_sync(
            {"question": "介绍一下自己", "answer": "我是程序员。"},
            context=MagicMock()
        )
        assert result["rating"] == "需改进"
        assert result["score"] < 4

    def test_input_schema_validation(self):
        """Test that input schema is correctly defined."""
        schema = EvaluateInterviewAnswerInput
        assert schema.model_fields["question"].is_required()
        assert schema.model_fields["answer"].is_required()
        assert schema.model_fields["category"].default == "技术"

    def test_category_field_preserved(self):
        """Test that category field is preserved in output."""
        result = self.tool._execute_sync(
            {"question": "问题", "answer": "答案内容足够长且使用了STAR法则来组织语言", "category": "行为"},
            context=MagicMock()
        )
        assert result["category"] == "行为"

    def test_question_field_preserved(self):
        """Test that question field is preserved in output."""
        result = self.tool._execute_sync(
            {"question": "请描述你的项目经验", "answer": "我在项目中负责后端开发。"},
            context=MagicMock()
        )
        assert result["question"] == "请描述你的项目经验"

    def test_suggestions_default_when_no_issues(self):
        """Test that default suggestion is '答案基本完整' when no issues."""
        result = self.tool._execute_sync(
            {"question": "项目经验", "answer": "我负责实现了一个完整的电商系统，使用微服务架构，完成了订单和支付模块的开发，项目上线后运行稳定，性能优秀。"},
            context=MagicMock()
        )
        assert "答案基本完整" in result["suggestions"]

    def test_score_capped_at_10(self):
        """Test that score is capped at 10."""
        result = self.tool._execute_sync(
            {"question": "详细描述", "answer": "我负责实现了一个大型电商系统，使用先进的微服务架构，通过性能优化和架构设计，使用缓存和异步处理，负责完成了订单、支付、用户、商品等多个核心模块，项目取得了优秀的成果和显著的业绩提升。"},
            context=MagicMock()
        )
        assert result["score"] <= 10