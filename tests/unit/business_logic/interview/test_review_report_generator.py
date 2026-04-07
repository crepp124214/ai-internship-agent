"""Tests for ReviewReportGenerator."""

import pytest
from src.business_logic.interview.review_report_generator import (
    ReviewReportDimension,
    ReviewReport,
    ReviewReportGenerator,
)


class TestReviewReportDimension:
    def test_dimension_has_required_fields(self):
        dim = ReviewReportDimension(
            name="技术深度",
            score=85,
            findings=["深入理解底层原理", "缺乏系统设计经验"],
            suggestions=["加强分布式系统学习", "补充实际项目经验"],
        )
        assert dim.name == "技术深度"
        assert dim.score == 85
        assert len(dim.findings) == 2
        assert len(dim.suggestions) == 2

    def test_dimension_defaults_to_empty_lists(self):
        dim = ReviewReportDimension(name="沟通能力", score=70)
        assert dim.findings == []
        assert dim.suggestions == []


class TestReviewReport:
    def test_report_has_required_fields(self):
        dimensions = [
            ReviewReportDimension(name="技术深度", score=80),
            ReviewReportDimension(name="逻辑表达", score=75),
        ]
        report = ReviewReport(
            overall_score=78,
            dimensions=dimensions,
            summary="整体表现良好",
            markdown="# 面试复盘报告\n\n...",
        )
        assert report.overall_score == 78
        assert len(report.dimensions) == 2
        assert "面试复盘报告" in report.markdown

    def test_report_markdown_contains_all_dimensions(self):
        dimensions = [
            ReviewReportDimension(name="技术深度", score=80),
            ReviewReportDimension(name="逻辑表达", score=75),
            ReviewReportDimension(name="岗位匹配度", score=82),
            ReviewReportDimension(name="沟通能力", score=78),
        ]
        markdown_content = """# 面试复盘报告

## 总体评分

**综合得分：79/100**

## 维度评分

### 技术深度
[▓▓▓▓▓▓▓▓░░] 80/100

### 逻辑表达
[▓▓▓▓▓▓▓░░░] 75/100

### 岗位匹配度
[▓▓▓▓▓▓▓▓░░] 82/100

### 沟通能力
[▓▓▓▓▓▓▓▓░░] 78/100

## 改进建议

- [技术深度] 深入理解核心技术原理
"""
        report = ReviewReport(
            overall_score=79,
            dimensions=dimensions,
            summary="整体表现良好",
            markdown=markdown_content,
        )
        for dim in dimensions:
            assert dim.name in report.markdown


class TestReviewReportGenerator:
    def setup_method(self):
        self.generator = ReviewReportGenerator()

    def test_generate_returns_review_report(self):
        answers = [
            {"question": "请描述你的项目经历", "answer": "我做了一个电商网站", "score": 80},
            {"question": "FastAPI中间件机制是什么", "answer": "中间件是...", "score": 75},
        ]
        report = self.generator.generate(answers)
        assert isinstance(report, ReviewReport)
        assert report.overall_score > 0

    def test_generate_with_empty_answers(self):
        answers = []
        report = self.generator.generate(answers)
        assert isinstance(report, ReviewReport)
        assert report.overall_score == 0

    def test_generate_calculates_four_dimensions(self):
        answers = [
            {"question": "项目相关", "answer": "回答1", "score": 85},
            {"question": "技术问题", "answer": "回答2", "score": 80},
            {"question": "匹配度问题", "answer": "回答3", "score": 75},
            {"question": "沟通问题", "answer": "回答4", "score": 70},
        ]
        report = self.generator.generate(answers)
        assert len(report.dimensions) == 4
        dimension_names = [d.name for d in report.dimensions]
        assert "技术深度" in dimension_names
        assert "逻辑表达" in dimension_names
        assert "岗位匹配度" in dimension_names
        assert "沟通能力" in dimension_names

    def test_generate_markdown_is_structured(self):
        answers = [
            {"question": "请介绍一下自己", "answer": "我是...", "score": 80},
        ]
        report = self.generator.generate(answers)
        assert "# 面试复盘报告" in report.markdown
        assert "## 总体评分" in report.markdown
        assert "## 维度评分" in report.markdown
        assert "## 改进建议" in report.markdown

    def test_dimension_scores_are_bounded(self):
        answers = [
            {"question": "Q1", "answer": "A1", "score": 150},
            {"question": "Q2", "answer": "A2", "score": -10},
        ]
        report = self.generator.generate(answers)
        for dim in report.dimensions:
            assert 0 <= dim.score <= 100

    def test_generate_preserves_summary(self):
        answers = [
            {"question": "Q1", "answer": "A1", "score": 85},
        ]
        report = self.generator.generate(answers)
        assert report.summary is not None
        assert len(report.summary) > 0
