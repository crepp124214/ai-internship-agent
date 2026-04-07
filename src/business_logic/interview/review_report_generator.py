"""Review Report Generator for AI Interview Coach.

Generates structured review reports with dimension scoring for interview practice.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ReviewReportDimension:
    """A single dimension score in the review report."""

    name: str
    score: int
    findings: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


@dataclass
class ReviewReport:
    """Complete review report for an interview session."""

    overall_score: int
    dimensions: list[ReviewReportDimension]
    summary: str
    markdown: str


class ReviewReportGenerator:
    """Generates structured review reports from interview answers."""

    DIMENSIONS = ["技术深度", "逻辑表达", "岗位匹配度", "沟通能力"]

    def generate(self, answers: list[dict[str, Any]]) -> ReviewReport:
        """Generate a review report from interview answers.

        Args:
            answers: List of dicts with keys "question", "answer", "score"

        Returns:
            ReviewReport with dimension scores and markdown output
        """
        if not answers:
            return self._create_empty_report()

        # Calculate overall score as weighted average
        total_score = sum(answer.get("score", 0) for answer in answers)
        overall_score = round(total_score / len(answers))

        # Bound overall score to 0-100
        overall_score = max(0, min(100, overall_score))

        # Generate dimension scores
        dimensions = self._generate_dimensions(answers)

        # Generate summary
        summary = self._generate_summary(overall_score, dimensions)

        # Generate markdown report
        markdown = self._generate_markdown(overall_score, dimensions, summary)

        return ReviewReport(
            overall_score=overall_score,
            dimensions=dimensions,
            summary=summary,
            markdown=markdown,
        )

    def _create_empty_report(self) -> ReviewReport:
        """Create an empty report for no answers."""
        dimensions = [
            ReviewReportDimension(name=name, score=0)
            for name in self.DIMENSIONS
        ]
        markdown = self._generate_markdown(0, dimensions, "暂无面试数据")
        return ReviewReport(
            overall_score=0,
            dimensions=dimensions,
            summary="暂无面试数据",
            markdown=markdown,
        )

    def _generate_dimensions(
        self, answers: list[dict[str, Any]]
    ) -> list[ReviewReportDimension]:
        """Generate dimension scores based on answers."""
        if not answers:
            return [
                ReviewReportDimension(name=name, score=0)
                for name in self.DIMENSIONS
            ]

        scores = [answer.get("score", 0) for answer in answers]
        avg_score = sum(scores) / len(scores) if scores else 0

        # Distribute scores across dimensions with some variance
        dimension_scores = []
        for i, dim_name in enumerate(self.DIMENSIONS):
            # Apply variance based on dimension type
            if dim_name == "技术深度":
                # Technical answers get higher weight
                variance = 10
                dim_avg = self._calculate_weighted_score(answers, ["技术", "项目", "架构"], variance)
            elif dim_name == "逻辑表达":
                # Logic/structure focused
                variance = 8
                dim_avg = self._calculate_weighted_score(answers, ["描述", "解释", "说明"], variance)
            elif dim_name == "岗位匹配度":
                # Job relevance
                variance = 12
                dim_avg = self._calculate_weighted_score(answers, ["岗位", "JD", "匹配"], variance)
            else:  # 沟通能力
                # Communication
                variance = 7
                dim_avg = self._calculate_weighted_score(answers, ["沟通", "团队", "协作"], variance)

            # Bound score to 0-100
            dim_score = max(0, min(100, round(dim_avg)))
            dimension_scores.append(dim_score)

        # Ensure overall consistency - dimension scores should roughly match overall
        total_dim_score = sum(dimension_scores)
        if total_dim_score > 0:
            scale_factor = (avg_score * 4) / total_dim_score
            dimension_scores = [
                round(s * scale_factor) for s in dimension_scores
            ]

        # Generate findings and suggestions for each dimension
        dimensions = []
        for i, dim_name in enumerate(self.DIMENSIONS):
            score = dimension_scores[i]
            findings = self._generate_findings(dim_name, score, answers)
            suggestions = self._generate_suggestions(dim_name, score)
            dimensions.append(
                ReviewReportDimension(
                    name=dim_name,
                    score=score,
                    findings=findings,
                    suggestions=suggestions,
                )
            )

        return dimensions

    def _calculate_weighted_score(
        self, answers: list[dict[str, Any]], keywords: list[str], variance: float
    ) -> float:
        """Calculate weighted score based on keywords."""
        if not answers:
            return 0

        total_weighted = 0
        total_weight = 0

        for answer in answers:
            score = answer.get("score", 0)
            question = answer.get("question", "").lower()

            # Calculate weight based on keyword matches
            weight = 1.0
            for keyword in keywords:
                if keyword.lower() in question:
                    weight += 0.5

            total_weighted += score * weight
            total_weight += weight

        if total_weight == 0:
            return sum(a.get("score", 0) for a in answers) / len(answers)

        base_score = total_weighted / total_weight

        # Add some variance
        import random
        variance_amount = random.uniform(-variance, variance)
        return base_score + variance_amount

    def _generate_findings(
        self, dimension: str, score: int, answers: list[dict[str, Any]]
    ) -> list[str]:
        """Generate findings for a dimension."""
        findings = []

        if score >= 80:
            findings.append(f"{dimension}表现优秀")
        elif score >= 60:
            findings.append(f"{dimension}表现良好")
        else:
            findings.append(f"{dimension}有待提升")

        # Add specific findings based on answers
        for answer in answers:
            question = answer.get("question", "")
            answer_text = answer.get("answer", "")

            if dimension == "技术深度" and any(
                kw in question.lower() for kw in ["技术", "项目", "架构"]
            ):
                if len(answer_text) > 50:
                    findings.append("回答详细且有深度")
                else:
                    findings.append("回答可以更详细")

            elif dimension == "逻辑表达" and any(
                kw in question.lower() for kw in ["描述", "解释", "说明"]
            ):
                findings.append("表达清晰有条理")

        return list(set(findings))[:3]  # Dedupe and limit

    def _generate_suggestions(self, dimension: str, score: int) -> list[str]:
        """Generate improvement suggestions for a dimension."""
        suggestions = []

        if score < 80:
            if dimension == "技术深度":
                suggestions.append("深入理解核心技术原理")
                suggestions.append("补充项目中的技术细节")
            elif dimension == "逻辑表达":
                suggestions.append("使用STAR法则组织答案")
                suggestions.append("注意答案的逻辑结构")
            elif dimension == "岗位匹配度":
                suggestions.append("多了解目标岗位的技能要求")
                suggestions.append("突出与岗位相关的经历")
            elif dimension == "沟通能力":
                suggestions.append("保持积极自信的态度")
                suggestions.append("注意语速和表达的清晰度")

        return suggestions[:3]  # Limit to 3

    def _generate_summary(
        self, overall_score: int, dimensions: list[ReviewReportDimension]
    ) -> str:
        """Generate overall summary text."""
        if overall_score >= 80:
            summary = "整体表现优秀，已具备该岗位的基本要求"
        elif overall_score >= 60:
            summary = "整体表现良好，部分维度需要继续提升"
        else:
            summary = "整体表现有待提升，建议系统复习相关知识"

        # Add dimension-specific summary
        low_dimensions = [d for d in dimensions if d.score < 60]
        if low_dimensions:
            low_names = "、".join([d.name for d in low_dimensions])
            summary += f"，特别是{low_names}方面"

        return summary

    def _generate_markdown(
        self,
        overall_score: int,
        dimensions: list[ReviewReportDimension],
        summary: str,
    ) -> str:
        """Generate markdown-formatted report."""
        lines = [
            "# 面试复盘报告",
            "",
            "## 总体评分",
            f"",
            f"**综合得分：{overall_score}/100**",
            "",
            f"**总结：** {summary}",
            "",
            "## 维度评分",
            "",
        ]

        # Add dimension scores
        for dim in dimensions:
            score_bar = "▓" * (dim.score // 10) + "░" * (10 - dim.score // 10)
            lines.append(f"### {dim.name}")
            lines.append(f"[{score_bar}] {dim.score}/100")
            lines.append("")

            if dim.findings:
                lines.append("**发现：**")
                for finding in dim.findings:
                    lines.append(f"- {finding}")
                lines.append("")

            if dim.suggestions:
                lines.append("**改进建议：**")
                for suggestion in dim.suggestions:
                    lines.append(f"- {suggestion}")
                lines.append("")

        # Add top-level improvement suggestions section
        lines.append("## 改进建议")
        lines.append("")
        all_suggestions = []
        for dim in dimensions:
            for suggestion in dim.suggestions:
                all_suggestions.append(f"- [{dim.name}] {suggestion}")
        if all_suggestions:
            lines.extend(all_suggestions)
        else:
            lines.append("继续保持当前表现，注意细节优化。")
        lines.append("")

        lines.append("---")
        lines.append("*本报告由 AI 面试教练自动生成*")

        return "\n".join(lines)
