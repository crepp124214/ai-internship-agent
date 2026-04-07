# Phase 7.5：数据初始化 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 支持 PDF/DOCX 简历上传、CSV/Excel JD 批量导入、示例数据一键初始化

**Architecture:** 简历通过 PyPDF2/python-docx 解析，JD 通过 pandas 解析，API 层统一处理上传和存储

**Tech Stack:** Python 3.10+, FastAPI, PyPDF2, python-docx, pandas, SQLAlchemy 2.0

---

## 文件结构

```
src/data_access/parsers/
  __init__.py                    # 新增
  resume_parser.py               # 新增：简历文件解析
  jd_parser.py                   # 新增：JD 批量导入解析

src/presentation/api/v1/
  import.py                      # 新增：导入 API 端点

scripts/
  seed_demo.py                   # 修改：增加示例数据

frontend/src/pages/components/
  DataImportModal.tsx           # 新增：导入弹窗组件
```

---

## Task 1: ResumeParser 简历解析器

**Files:**
- Create: `src/data_access/parsers/__init__.py`
- Create: `src/data_access/parsers/resume_parser.py`
- Test: `tests/unit/data_access/test_resume_parser.py`

- [ ] **Step 1: 创建 parsers/__init__.py**

```python
# src/data_access/parsers/__init__.py
from src.data_access.parsers.resume_parser import ResumeParser, ResumeParseResult
from src.data_access.parsers.jd_parser import JDParser, JDParseResult

__all__ = ["ResumeParser", "ResumeParseResult", "JDParser", "JDParseResult"]
```

- [ ] **Step 2: 创建 ResumeParser 类**

```python
# src/data_access/parsers/resume_parser.py
"""简历文件解析器，支持 PDF 和 DOCX 格式"""
from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel


@dataclass
class ResumeParseResult:
    """解析结果"""
    name: Optional[str] = None
    education: Optional[str] = None
    skills: list[str] = None
    experience: Optional[str] = None
    raw_text: str = ""


class ResumeParser:
    """简历文件解析器"""

    def parse(self, file_content: bytes, filename: str) -> ResumeParseResult:
        """
        解析简历文件
        
        Args:
            file_content: 文件二进制内容
            filename: 文件名（用于判断格式）
        
        Returns:
            ResumeParseResult: 解析结果
        """
        ext = filename.lower().split('.')[-1]
        
        if ext == 'pdf':
            return self._parse_pdf(file_content)
        elif ext in ('docx', 'doc'):
            return self._parse_docx(file_content)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def _parse_pdf(self, content: bytes) -> ResumeParseResult:
        """解析 PDF 文件"""
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(io.BytesIO(content))
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
        except ImportError:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
        
        return self._extract_structured_info(text)

    def _parse_docx(self, content: bytes) -> ResumeParseResult:
        """解析 DOCX 文件"""
        try:
            import docx
            doc = docx.Document(io.BytesIO(content))
            text = "\n".join([p.text for p in doc.paragraphs])
        except ImportError:
            raise ImportError("python-docx is required to parse .docx files")
        
        return self._extract_structured_info(text)

    def _extract_structured_info(self, text: str) -> ResumeParseResult:
        """从文本中提取结构化信息"""
        import re
        
        result = ResumeParseResult(raw_text=text)
        
        # 提取姓名（假设在第一行或以"姓名"开头）
        lines = text.strip().split('\n')
        if lines:
            first_line = lines[0].strip()
            if not first_line.startswith('姓名') and len(first_line) < 10:
                result.name = first_line
        
        name_match = re.search(r'姓名[：:]\s*(\S+)', text)
        if name_match:
            result.name = name_match.group(1)
        
        # 提取学历
        edu_keywords = ['博士', '硕士', '本科', '大专', '高中', '中专']
        for keyword in edu_keywords:
            if keyword in text:
                result.education = keyword
                break
        
        # 提取技能（简单关键词匹配）
        skill_keywords = [
            'Python', 'Java', 'JavaScript', 'TypeScript', 'Go', 'Rust',
            'C++', 'C#', 'React', 'Vue', 'Angular', 'Django', 'FastAPI',
            'Spring', 'Node.js', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis',
            'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP', 'TensorFlow',
            'PyTorch', 'LangChain', 'Linux', 'Git', 'Agile', 'Scrum'
        ]
        
        result.skills = [s for s in skill_keywords if s in text]
        
        # 提取经验（简单匹配）
        exp_match = re.search(r'(\d+)\s*年', text)
        if exp_match:
            years = int(exp_match.group(1))
            result.experience = f"{years}年"
        
        return result
```

- [ ] **Step 3: 创建单元测试**

```python
# tests/unit/data_access/test_resume_parser.py
import pytest
from src.data_access.parsers.resume_parser import ResumeParser, ResumeParseResult


class TestResumeParser:
    def test_parse_result_defaults(self):
        """测试默认解析结果"""
        result = ResumeParseResult()
        assert result.name is None
        assert result.skills == []
        assert result.raw_text == ""

    def test_extract_skills(self):
        """测试技能提取"""
        parser = ResumeParser()
        text = "熟悉 Python、Java、Django 和 PostgreSQL"
        result = parser._extract_structured_info(text)
        
        assert "Python" in result.skills
        assert "Java" in result.skills
        assert "Django" in result.skills
        assert "PostgreSQL" in result.skills

    def test_extract_education(self):
        """测试学历提取"""
        parser = ResumeParser()
        text = "清华大学 硕士 2020-2023"
        result = parser._extract_structured_info(text)
        
        assert result.education == "硕士"

    def test_extract_experience(self):
        """测试经验提取"""
        parser = ResumeParser()
        text = "有 3 年 Python 开发经验"
        result = parser._extract_structured_info(text)
        
        assert result.experience == "3年"
```

- [ ] **Step 4: 运行测试**

Run: `pytest tests/unit/data_access/test_resume_parser.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/data_access/parsers/__init__.py src/data_access/parsers/resume_parser.py tests/unit/data_access/test_resume_parser.py
git commit -m "feat(data_init): 添加 ResumeParser 简历解析器"
```

---

## Task 2: JDParser JD 解析器

**Files:**
- Create: `src/data_access/parsers/jd_parser.py`
- Test: `tests/unit/data_access/test_jd_parser.py`

- [ ] **Step 1: 创建 JDParser 类**

```python
# src/data_access/parsers/jd_parser.py
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
        """
        解析 JD 文件（CSV 或 Excel）
        
        Args:
            file_content: 文件二进制内容
            filename: 文件名
        
        Returns:
            list[JDParseResult]: 解析结果列表
        """
        ext = filename.lower().split('.')[-1]
        
        if ext == 'csv':
            return self._parse_csv(file_content)
        elif ext in ('xlsx', 'xls'):
            return self._parse_excel(file_content)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def _parse_csv(self, content: bytes) -> list[JDParseResult]:
        """解析 CSV 文件"""
        df = pd.read_csv(io.BytesIO(content))
        return self._parse_dataframe(df)

    def _parse_excel(self, content: bytes) -> list[JDParseResult]:
        """解析 Excel 文件"""
        df = pd.read_excel(io.BytesIO(content))
        return self._parse_dataframe(df)

    def _parse_dataframe(self, df: pd.DataFrame) -> list[JDParseResult]:
        """从 DataFrame 解析 JD 列表"""
        results = []
        
        # 字段映射
        column_mapping = {
            'title': ['title', '岗位名称', '职位名称', 'job_title', 'position'],
            'company': ['company', '公司名称', 'company_name', 'employer'],
            'description': ['description', '岗位描述', 'job_description', 'desc'],
            'requirements': ['requirements', '任职要求', 'requirement', 'qualifications'],
            'location': ['location', '工作地点', 'city', '地点'],
            'salary': ['salary', '薪资', '工资', 'compensation'],
        }
        
        # 找到实际列名
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
        """查找实际列名"""
        for col in columns:
            col_lower = str(col).lower()
            if field.lower() in col_lower:
                return col
        return field

    def _get_value(self, row, column) -> any:
        """安全获取列值"""
        if column in row.index:
            val = row[column]
            return val if pd.notna(val) else None
        return None
```

- [ ] **Step 2: 创建单元测试**

```python
# tests/unit/data_access/test_jd_parser.py
import pytest
import pandas as pd
from io import BytesIO
from src.data_access.parsers.jd_parser import JDParser, JDParseResult


class TestJDParser:
    def test_parse_result(self):
        """测试 JD 解析结果"""
        result = JDParseResult(
            title="Python Developer",
            company="TechCorp",
            description="We need a Python developer",
        )
        
        assert result.title == "Python Developer"
        assert result.company == "TechCorp"

    def test_parse_csv_basic(self):
        """测试 CSV 解析"""
        csv_content = b"title,company,description\nPython Developer,TechCorp,We need Python"
        parser = JDParser()
        results = parser._parse_csv(csv_content)
        
        assert len(results) == 1
        assert results[0].title == "Python Developer"
        assert results[0].company == "TechCorp"

    def test_find_column(self):
        """测试列名查找"""
        parser = JDParser()
        columns = ['岗位名称', '公司名称', '描述']
        
        assert parser._find_column('title', columns) == '岗位名称'
        assert parser._find_column('company', columns) == '公司名称'
```

- [ ] **Step 3: 运行测试**

Run: `pytest tests/unit/data_access/test_jd_parser.py -v`
Expected: PASS

- [ ] **Step 4: 提交**

```bash
git add src/data_access/parsers/jd_parser.py tests/unit/data_access/test_jd_parser.py
git commit -m "feat(data_init): 添加 JDParser JD 解析器"
```

---

## Task 3: Import API 端点

**Files:**
- Create: `src/presentation/api/v1/import.py`
- Test: `tests/integration/api/test_import.py`

- [ ] **Step 1: 创建 Import API**

```python
# src/presentation/api/v1/import.py
"""数据导入 API"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from src.data_access.parsers.resume_parser import ResumeParser
from src.data_access.parsers.jd_parser import JDParser
from src.data_access.repositories.resume_repository import resume_repository
from src.data_access.repositories.job_repository import job_repository
from src.presentation.api.deps import get_current_user, get_db

router = APIRouter()


@router.post("/resume")
async def import_resume(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    导入简历（PDF 或 DOCX）
    """
    parser = ResumeParser()
    
    try:
        content = await file.read()
        result = parser.parse(content, file.filename)
        
        # 存储到数据库
        resume = resume_repository.create(db, {
            "user_id": current_user.id,
            "title": result.name or "未命名简历",
            "resume_text": result.raw_text,
            "processed_content": result.raw_text,
        })
        
        return {
            "success": True,
            "resume_id": resume.id,
            "parsed": {
                "name": result.name,
                "education": result.education,
                "skills": result.skills,
                "experience": result.experience,
            }
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )


@router.post("/jds")
async def import_jds(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    批量导入 JD（CSV 或 Excel）
    """
    parser = JDParser()
    
    try:
        content = await file.read()
        results = parser.parse_file(content, file.filename)
        
        imported = 0
        failed = 0
        errors = []
        
        for idx, jd_data in enumerate(results):
            try:
                job_repository.create(db, {
                    "user_id": current_user.id,
                    "title": jd_data.title,
                    "company": jd_data.company,
                    "description": jd_data.description,
                    "requirements": jd_data.requirements,
                    "location": jd_data.location,
                    "salary": jd_data.salary,
                })
                imported += 1
            except Exception:
                failed += 1
                errors.append(f"Row {idx + 1}: Failed to import '{jd_data.title}'")
        
        return {
            "success": True,
            "total": len(results),
            "imported": imported,
            "failed": failed,
            "errors": errors,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )
```

- [ ] **Step 2: 运行现有测试确认无回归**

Run: `pytest tests/integration/api/ -v --tb=short 2>&1 | tail -20`
Expected: PASS

- [ ] **Step 3: 提交**

```bash
git add src/presentation/api/v1/import.py
git commit -m "feat(api): 添加简历和 JD 导入 API 端点"
```

---

## Task 4: 增强 seed_demo.py 示例数据

**Files:**
- Modify: `scripts/seed_demo.py`

- [ ] **Step 1: 读取现有 seed_demo.py**

Read: `scripts/seed_demo.py`

- [ ] **Step 2: 添加示例简历和 JD 数据**

在 `main()` 函数中添加：

```python
def seed_example_data(db: Session):
    """创建示例数据"""
    
    # 示例简历
    resumes = [
        {
            "title": "张三 - Python 开发工程师",
            "resume_text": """姓名：张三
学历：本科 - 计算机科学 - 清华大学 2016-2020

技能：
- Python、Django、FastAPI
- PostgreSQL、Redis、MongoDB
- Docker、Kubernetes
- AWS 云服务
- Git、JIRA

经历：
百度 - 后端开发工程师 2020-至今
- 负责搜索服务开发，使用 Python + FastAPI
- 优化查询性能，提升 50% 响应速度
- 设计并实现微服务架构""",
            "processed_content": """姓名：张三
学历：本科 - 计算机科学 - 清华大学 2016-2020

技能：Python, Django, FastAPI, PostgreSQL, Redis, MongoDB, Docker, Kubernetes, AWS

经历：百度 - 后端开发工程师 2020-至今
- 负责搜索服务开发，使用 Python + FastAPI
- 优化查询性能，提升 50% 响应速度
- 设计并实现微服务架构""",
        },
        {
            "title": "李四 - 数据分析师",
            "resume_text": """姓名：李四
学历：硕士 - 数据科学 - 上海交通大学 2018-2021

技能：
- Python、R、SQL
- Pandas、NumPy、Matplotlib
- TensorFlow、PyTorch
- Tableau、PowerBI
- Spark、Hadoop

经历：字节跳动 - 数据分析师 2021-至今
- 分析用户行为数据，提供业务洞察
- 建立数据管道，处理 TB 级数据
- 使用机器学习预测用户留存""",
            "processed_content": """姓名：李四
学历：硕士 - 数据科学 - 上海交通大学 2018-2021

技能：Python, R, SQL, Pandas, NumPy, TensorFlow, PyTorch, Spark, Hadoop

经历：字节跳动 - 数据分析师 2021-至今
- 分析用户行为数据，提供业务洞察
- 建立数据管道，处理 TB 级数据""",
        },
    ]
    
    # 示例 JD
    jobs = [
        {
            "title": "Python 后端开发工程师",
            "company": "字节跳动",
            "description": "负责抖音后端服务开发，使用 Python + Go 语言",
            "requirements": "3年以上 Python 开发经验，熟悉 Django 或 FastAPI",
            "location": "北京",
            "salary": "30-50K",
        },
        {
            "title": "AI 算法工程师",
            "company": "商汤科技",
            "description": "负责计算机视觉算法研发，推动 AI 技术落地",
            "requirements": "硕士及以上，熟悉 PyTorch/TensorFlow，有顶会论文优先",
            "location": "上海",
            "salary": "40-60K",
        },
        {
            "title": "前端开发工程师",
            "company": "腾讯",
            "description": "负责微信小程序和 Web 端开发",
            "requirements": "3年以上前端经验，熟悉 React 或 Vue",
            "location": "深圳",
            "salary": "25-45K",
        },
        {
            "title": "数据分析师",
            "company": "美团",
            "description": "挖掘用户数据，提供商业洞察",
            "requirements": "熟练使用 SQL 和 Python，有数据分析经验",
            "location": "北京",
            "salary": "20-35K",
        },
        {
            "title": "DevOps 工程师",
            "company": "阿里云",
            "description": "负责云原生基础设施建设",
            "requirements": "熟悉 Docker、Kubernetes，有大规模运维经验",
            "location": "杭州",
            "salary": "35-55K",
        },
    ]
    
    # 插入数据
    from src.data_access.repositories.resume_repository import resume_repository
    from src.data_access.repositories.job_repository import job_repository
    
    for resume_data in resumes:
        existing = resume_repository.get_by_user_and_title(
            db, user_id=1, title=resume_data["title"]
        )
        if not existing:
            resume_repository.create(db, {**resume_data, "user_id": 1})
    
    for job_data in jobs:
        existing = job_repository.get_by_user_and_title(
            db, user_id=1, title=job_data["title"]
        )
        if not existing:
            job_repository.create(db, {**job_data, "user_id": 1})
```

- [ ] **Step 3: 在 main() 中调用**

在 `main()` 函数末尾添加：

```python
    # 创建示例数据
    print("Creating example data...")
    seed_example_data(db)
    print(f"Created {len(resumes)} resumes and {len(jobs)} jobs")
```

- [ ] **Step 4: 测试脚本**

Run: `python scripts/seed_demo.py 2>&1 | tail -20`
Expected: 运行成功，无错误

- [ ] **Step 5: 提交**

```bash
git add scripts/seed_demo.py
git commit -m "feat(data_init): 增强 seed_demo.py 示例数据"
```

---

## Task 5: DataImportModal 前端组件

**Files:**
- Create: `frontend/src/pages/components/DataImportModal.tsx`
- Test: `tests/integration/test_import_ui.py` (可选)

- [ ] **Step 1: 创建 DataImportModal 组件**

```tsx
// frontend/src/pages/components/DataImportModal.tsx
import React, { useState } from 'react';

interface DataImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImportSuccess: () => void;
}

export const DataImportModal: React.FC<DataImportModalProps> = ({
  isOpen,
  onClose,
  onImportSuccess,
}) => {
  const [activeTab, setActiveTab] = useState<'resume' | 'jd'>('resume');
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any>(null);

  if (!isOpen) return null;

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const endpoint = activeTab === 'resume' 
        ? '/api/v1/import/resume' 
        : '/api/v1/import/jds';

      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      const data = await response.json();
      setResult(data);

      if (data.success) {
        onImportSuccess();
      }
    } catch (error) {
      setResult({ success: false, error: String(error) });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-md p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">导入数据</h2>
          <button onClick={onClose} className="text-gray-500">×</button>
        </div>

        <div className="flex gap-2 mb-4">
          <button
            className={`px-4 py-2 rounded ${activeTab === 'resume' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
            onClick={() => setActiveTab('resume')}
          >
            简历导入
          </button>
          <button
            className={`px-4 py-2 rounded ${activeTab === 'jd' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
            onClick={() => setActiveTab('jd')}
          >
            JD 批量导入
          </button>
        </div>

        <div className="mb-4">
          <input
            type="file"
            accept={activeTab === 'resume' ? '.pdf,.docx' : '.csv,.xlsx'}
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="block w-full text-sm text-gray-500
              file:mr-4 file:py-2 file:px-4
              file:rounded file:border-0
              file:text-sm file:font-semibold
              file:bg-blue-50 file:text-blue-700"
          />
          <p className="text-xs text-gray-500 mt-1">
            {activeTab === 'resume' 
              ? '支持 PDF、DOCX 格式' 
              : '支持 CSV、Excel 格式'}
          </p>
        </div>

        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          className="w-full py-2 px-4 bg-blue-500 text-white rounded disabled:bg-gray-300"
        >
          {uploading ? '上传中...' : '上传'}
        </button>

        {result && (
          <div className={`mt-4 p-3 rounded ${result.success ? 'bg-green-100' : 'bg-red-100'}`}>
            {result.success ? (
              <p className="text-green-700">
                {activeTab === 'resume' 
                  ? `导入成功！简历 ID: ${result.resume_id}` 
                  : `导入成功！${result.imported}/${result.total} 条`}
              </p>
            ) : (
              <p className="text-red-700">导入失败：{result.error}</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/pages/components/DataImportModal.tsx
git commit -m "feat(frontend): 添加 DataImportModal 导入组件"
```

---

## Task 6: 示例数据加载按钮

**Files:**
- Modify: `frontend/src/pages/dashboard-page.tsx`

- [ ] **Step 1: 在 Dashboard 添加"加载示例数据"按钮**

在 dashboard-page.tsx 中添加：

```tsx
// 在现有组件中添加
const [showImportModal, setShowImportModal] = useState(false);

// 在 useEffect 中检测是否有数据
useEffect(() => {
  checkHasData();
}, []);

// 添加按钮
<button
  onClick={() => setShowImportModal(true)}
  className="px-4 py-2 bg-green-500 text-white rounded"
>
  导入数据
</button>

// 添加 Modal
<DataImportModal
  isOpen={showImportModal}
  onClose={() => setShowImportModal(false)}
  onImportSuccess={() => {
    setShowImportModal(false);
    // 刷新数据
  }}
/>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/pages/dashboard-page.tsx
git commit -m "feat(frontend): 在 Dashboard 添加数据导入入口"
```

---

## Task 7: 最终验证

- [ ] **Step 1: 运行完整测试**

Run: `python -m pytest --cov=src --cov-report=term 2>&1 | tail -15`
Expected: 覆盖率 ≥ 80%

- [ ] **Step 2: 验证 API 可用**

Run: `python -c "from src.presentation.api.v1.import import router; print('API OK')"`
Expected: 输出 "API OK"

- [ ] **Step 3: 验证解析器可用**

Run: `python -c "from src.data_access.parsers import ResumeParser, JDParser; print('Parsers OK')"`
Expected: 输出 "Parsers OK"

- [ ] **Step 4: 最终提交**

```bash
git add -A && git commit -m "feat(phase7.5): 完成数据初始化功能
- 添加 ResumeParser 支持 PDF/DOCX 解析
- 添加 JDParser 支持 CSV/Excel 解析
- 添加导入 API 端点
- 增强 seed_demo.py 示例数据
- 添加前端 DataImportModal 组件"
```

---

## 验收标准检查

- [ ] ResumeParser 可正确解析 PDF/DOCX
- [ ] JDParser 可正确解析 CSV/Excel
- [ ] 导入 API 返回正确格式
- [ ] seed_demo.py 包含 2-3 个简历 + 5 个 JD
- [ ] 前端可上传文件并显示结果
- [ ] 整体覆盖率不退步
