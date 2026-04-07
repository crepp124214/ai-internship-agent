"""简历文件解析器，支持 PDF 和 DOCX 格式"""
from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Optional


@dataclass
class ResumeParseResult:
    """解析结果"""
    name: Optional[str] = None
    education: Optional[str] = None
    skills: list[str] = None
    experience: Optional[str] = None
    raw_text: str = ""

    def __post_init__(self):
        if self.skills is None:
            self.skills = []


class ResumeParser:
    """简历文件解析器"""

    def parse(self, file_content: bytes, filename: str) -> ResumeParseResult:
        ext = filename.lower().split('.')[-1]

        if ext == 'pdf':
            return self._parse_pdf(file_content)
        elif ext in ('docx', 'doc'):
            return self._parse_docx(file_content)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def _parse_pdf(self, content: bytes) -> ResumeParseResult:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(content))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return self._extract_structured_info(text)

    def _parse_docx(self, content: bytes) -> ResumeParseResult:
        import docx
        doc = docx.Document(io.BytesIO(content))
        text = "\n".join([p.text for p in doc.paragraphs])
        return self._extract_structured_info(text)

    def _extract_structured_info(self, text: str) -> ResumeParseResult:
        import re

        result = ResumeParseResult(raw_text=text)

        lines = text.strip().split('\n')
        if lines:
            first_line = lines[0].strip()
            if not first_line.startswith('姓名') and len(first_line) < 10:
                result.name = first_line

        name_match = re.search(r'姓名[：:]\s*(\S+)', text)
        if name_match:
            result.name = name_match.group(1)

        edu_keywords = ['博士', '硕士', '本科', '大专', '高中', '中专']
        for keyword in edu_keywords:
            if keyword in text:
                result.education = keyword
                break

        skill_keywords = [
            'Python', 'Java', 'JavaScript', 'TypeScript', 'Go', 'Rust',
            'C++', 'C#', 'React', 'Vue', 'Angular', 'Django', 'FastAPI',
            'Spring', 'Node.js', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis',
            'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP', 'TensorFlow',
            'PyTorch', 'LangChain', 'Linux', 'Git'
        ]

        result.skills = [s for s in skill_keywords if s in text]

        exp_match = re.search(r'(\d+)\s*年', text)
        if exp_match:
            years = int(exp_match.group(1))
            result.experience = f"{years}年"

        return result