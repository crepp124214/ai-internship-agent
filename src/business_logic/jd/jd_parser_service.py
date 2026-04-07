# src/business_logic/jd/jd_parser_service.py
import re
from src.business_logic.jd.schemas import ParsedJD


class JdParserService:
    """解析 Job Description，提取结构化信息"""

    SKILL_KEYWORDS = [
        "python", "golang", "go", "java", "c++", "c#", "rust", "javascript",
        "typescript", "react", "vue", "angular", "node", "django", "fastapi",
        "flask", "spring", "mysql", "postgresql", "mongodb", "redis",
        "kafka", "rabbitmq", "docker", "kubernetes", "k8s", "aws", "gcp",
        "azure", "linux", "git", "ci/cd", "devops", "microservice", "微服务",
        "分布式", "缓存", "数据库", "sql", "nosql", "rest", "api", "graphql",
        "machine learning", "ml", "ai", "deep learning", "nlp", "tensorflow",
        "pytorch", "pandas", "numpy", "spark", "hadoop", "flink",
    ]

    def parse(self, jd_text: str) -> ParsedJD:
        if not jd_text or not jd_text.strip():
            return ParsedJD(
                company=None, position="", required_skills=[],
                qualifications=[], highlights=[], raw_text=""
            )

        lines = jd_text.strip().split("\n")
        company = self._extract_company(lines, jd_text)
        position = self._extract_position(lines)
        required_skills = self._extract_skills(jd_text)
        qualifications = self._extract_qualifications(jd_text)
        highlights = self._extract_highlights(jd_text)

        return ParsedJD(
            company=company,
            position=position,
            required_skills=required_skills,
            qualifications=qualifications,
            highlights=highlights,
            raw_text=jd_text,
        )

    def _extract_company(self, lines: list[str], raw_text: str) -> str | None:
        if lines:
            first_line = lines[0].strip()
            if "公司" in first_line or any(c in first_line for c in ["-", "–", "—"]):
                parts = re.split(r"[-–—]", first_line)
                if len(parts) >= 2:
                    return parts[0].strip()
        return None

    def _extract_position(self, lines: list[str]) -> str:
        for line in lines[:5]:
            line = line.strip()
            if "职位" in line and "：" in line:
                parts = line.split("：", 1)
                if len(parts) == 2:
                    return parts[1].strip()
            if re.match(r"^.*(工程师|开发者|设计师|产品|运营|实习|全职).*$", line):
                for sep in ["-", "–", "—", "："]:
                    if sep in line:
                        parts = line.split(sep, 1)
                        if len(parts) == 2:
                            return parts[1].strip()
        return ""

    def _extract_skills(self, text: str) -> list[str]:
        found = []
        for skill in self.SKILL_KEYWORDS:
            # Case-insensitive search but preserve the original text case
            pattern = re.escape(skill)
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                found.append(match.group())
        return list(set(found))

    def _extract_qualifications(self, text: str) -> list[str]:
        lines = text.split("\n")
        quals = []
        in_qual_section = False
        for line in lines:
            line = line.strip()
            if any(k in line for k in ["要求", "任职", "资格", "条件"]):
                in_qual_section = True
                continue
            if in_qual_section and line:
                if any(k in line for k in ["加分", "优先", "福利", "发展", "收获"]):
                    break
                if line.startswith("-"):
                    line = line[1:].strip()
                if line:
                    quals.append(line)
        return quals

    def _extract_highlights(self, text: str) -> list[str]:
        lines = text.split("\n")
        highlights = []
        for line in lines:
            line = line.strip()
            if any(k in line for k in ["加分", "优先", "亮点", "福利"]):
                if line.startswith("-") or line.startswith("•"):
                    line = line[1:].strip()
                highlights.append(line)
        return highlights