"""JD 批量导入解析器，支持 CSV 和 Excel 格式"""
from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Optional

import pandas as pd


@dataclass
class JDParseResult:
    """单条 JD 解析结果"""
    title: str
    company: str
    description: str
    requirements: Optional[str] = None
    location: Optional[str] = None
    salary: Optional[str] = None


class JDParser:
    """JD 批量导入解析器"""

    def parse_file(self, file_content: bytes, filename: str) -> list[JDParseResult]:
        ext = filename.lower().split('.')[-1]

        if ext == 'csv':
            return self._parse_csv(file_content)
        elif ext in ('xlsx', 'xls'):
            return self._parse_excel(file_content)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def _parse_csv(self, content: bytes) -> list[JDParseResult]:
        df = pd.read_csv(io.BytesIO(content))
        return self._parse_dataframe(df)

    def _parse_excel(self, content: bytes) -> list[JDParseResult]:
        df = pd.read_excel(io.BytesIO(content))
        return self._parse_dataframe(df)

    def _parse_dataframe(self, df: pd.DataFrame) -> list[JDParseResult]:
        results = []

        column_mapping = {
            'title': ['title', '岗位名称', '职位名称', 'job_title', 'position'],
            'company': ['company', '公司名称', 'company_name', 'employer'],
            'description': ['description', '岗位描述', 'job_description', 'desc'],
            'requirements': ['requirements', '任职要求', 'requirement', 'qualifications'],
            'location': ['location', '工作地点', 'city', '地点'],
            'salary': ['salary', '薪资', '工资', 'compensation'],
        }

        actual_columns = {col: self._find_column(col, df.columns) for col in column_mapping}

        for _, row in df.iterrows():
            try:
                title = self._get_value(row, actual_columns['title'])
                if not title:
                    continue

                result = JDParseResult(
                    title=str(title),
                    company=str(self._get_value(row, actual_columns['company']) or ""),
                    description=str(self._get_value(row, actual_columns['description']) or ""),
                    requirements=str(self._get_value(row, actual_columns['requirements']) or ""),
                    location=str(self._get_value(row, actual_columns['location']) or ""),
                    salary=str(self._get_value(row, actual_columns['salary']) or ""),
                )
                results.append(result)
            except Exception:
                continue

        return results

    def _find_column(self, field: str, columns) -> str:
        for col in columns:
            col_lower = str(col).lower()
            if field.lower() in col_lower:
                return col
        return field

    def _get_value(self, row, column) -> any:
        if column in row.index:
            val = row[column]
            return val if pd.notna(val) else None
        return None