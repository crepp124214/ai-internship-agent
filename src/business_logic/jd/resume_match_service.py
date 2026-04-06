from src.business_logic.jd.schemas import ParsedJD, MatchReport


class ResumeMatchService:
    """计算简历与 JD 的匹配度"""

    def compute_match(self, resume_text: str, parsed_jd: ParsedJD) -> MatchReport:
        keyword_coverage = self._compute_keyword_coverage(
            resume_text, parsed_jd.required_skills
        )
        match_score = self._compute_match_score(keyword_coverage)
        gaps = self._identify_gaps(keyword_coverage, parsed_jd.qualifications)
        suggestions = self._generate_suggestions(gaps, parsed_jd.highlights)
        return MatchReport(
            keyword_coverage=keyword_coverage,
            match_score=match_score,
            gaps=gaps,
            suggestions=suggestions,
        )

    def _compute_keyword_coverage(
        self, resume_text: str, required_skills: list[str]
    ) -> dict[str, bool]:
        resume_lower = resume_text.lower()
        return {skill: skill.lower() in resume_lower for skill in required_skills}

    def _compute_match_score(self, keyword_coverage: dict[str, bool]) -> float:
        if not keyword_coverage:
            return 0.0
        covered = sum(keyword_coverage.values())
        return covered / len(keyword_coverage)

    def _identify_gaps(
        self, keyword_coverage: dict[str, bool], qualifications: list[str]
    ) -> list[str]:
        uncovered = [skill for skill, covered in keyword_coverage.items() if not covered]
        return uncovered

    def _generate_suggestions(self, gaps: list[str], highlights: list[str]) -> list[str]:
        suggestions = []
        for gap in gaps:
            suggestions.append(f"建议在简历中突出与 {gap} 相关的项目经验或技能描述")
        if highlights:
            suggestions.append(f"职位亮点：{highlights[0]}，可作为简历加分项强调")
        return suggestions
