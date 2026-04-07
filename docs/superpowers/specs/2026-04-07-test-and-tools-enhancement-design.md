# Phase 7：测试覆盖率提升 + 工具库扩展 设计文档

> 版本: v1.0.0 | 状态: 设计完成 | 日期: 2026-04-07

---

## 一、目标

1. **测试覆盖率**：从当前 46.87% 提升至 ≥80%
2. **工具库扩展**：从 2 个工具扩展至 13 个工具
3. **ToolContext 架构**：统一工具依赖管理，提升可测试性
4. **Agent 改造**：将 ResumeCustomizerAgent 改造为 ReAct 模式

---

## 二、实施方案

采用**功能驱动式**（方案 B）：以工具扩展为主线，测试跟随功能走。

### 时间线

| 阶段 | 内容 | 目标 |
|------|------|------|
| Week 1-2 | ToolContext + 6 个高优先级工具 + 工具层测试 | 工具数 2→8，工具层覆盖率 85%+ |
| Week 3-4 | 5 个扩展工具 + ResumeCustomizerAgent 改造 + Agent 层测试 | 工具数 8→13，Agent 层覆盖率 75%+ |
| Week 5-6 | 全面补齐低覆盖率模块 | 整体覆盖率 80%+ |

---

## 三、ToolContext 架构设计

### 3.1 核心问题

当前工具直接调用 `next(get_db())`，存在：
- 依赖隐式获取，难以测试
- 无法统一管理事务
- 无法注入 mock 依赖
- 工具间无法共享上下文

### 3.2 ToolContext 定义

```python
# src/core/tools/tool_context.py
from dataclasses import dataclass, field
from typing import Optional, Any
from sqlalchemy.orm import Session

@dataclass
class ToolContext:
    """工具执行上下文，统一管理依赖"""
    db: Session
    user_id: Optional[int] = None
    agent_id: Optional[str] = None
    session_id: Optional[str] = None
    cache: dict[str, Any] = field(default_factory=dict)
```

### 3.3 BaseTool 改造

```python
# src/core/tools/base_tool.py
class BaseTool(BaseModel):
    name: str
    description: str
    args_schema: Type[BaseModel] = None

    def _execute(self, **kwargs) -> dict:
        raise NotImplementedError

    def _run(self, tool_input: dict, context: ToolContext) -> Any:
        if self.args_schema:
            validated = self.args_schema(**tool_input)
            kwargs = validated.dict()
        else:
            kwargs = tool_input
        kwargs['context'] = context
        try:
            return self._execute(**kwargs)
        except Exception as e:
            return {"error": str(e), "tool": self.name}
```

### 3.4 ToolRegistry 改造

```python
# src/core/runtime/tool_registry.py
class ToolRegistry:
    def execute(self, name: str, tool_input: dict, context: ToolContext) -> Any:
        tool = self.get_tool(name)
        return tool._run(tool_input, context)
```

### 3.5 工具实现示例

```python
class ReadResumeTool(BaseTool):
    name = "read_resume"
    description = "读取简历内容"
    args_schema = ReadResumeInput

    def _execute(self, resume_id: int, context: ToolContext) -> dict:
        from src.data_access.repositories import resume_repository
        resume = resume_repository.get_by_id(context.db, resume_id)
        if not resume:
            return {"error": f"Resume {resume_id} not found"}
        return {
            "resume_id": resume_id,
            "resume_text": resume.processed_content or resume.resume_text,
            "title": resume.title,
        }
```

---

## 四、工具库扩展规划

### 4.1 现有工具（2个）

| 工具名 | 描述 | 文件 |
|--------|------|------|
| read_resume | 读取简历完整内容 | `src/business_logic/jd/tools/read_resume.py` |
| match_resume_to_job | 分析简历与岗位匹配度 | `src/business_logic/jd/tools/match_resume_to_job.py` |

### 4.2 Week 1-2 新增工具（6个）

| 工具名 | 描述 | 类别 |
|--------|------|------|
| update_resume | 更新简历内容（标题、技能、经历） | Resume |
| analyze_resume_skills | 提取并分析简历技能标签 | Resume |
| search_jobs | 根据关键词搜索岗位 | Job |
| analyze_jd | 深度解析 JD（技能要求、薪资范围） | Job |
| generate_interview_questions | 根据 JD 和简历生成面试题 | Interview |
| web_search | 网络搜索（公司信息、行业动态） | 通用 |

### 4.3 Week 3-4 新增工具（5个）

| 工具名 | 描述 | 类别 |
|--------|------|------|
| format_resume | 格式化简历（Markdown → 结构化输出） | Resume |
| compare_resumes | 对比两个简历版本的差异 | Resume |
| calculate_job_match | 计算简历与岗位匹配度（数值化） | Job |
| evaluate_interview_answer | 评估面试答案质量 | Interview |
| extract_keywords | 从文本中提取关键词 | 通用 |

### 4.4 文件结构

```
src/core/tools/
  tool_context.py          # ToolContext 定义（新增）
  base_tool.py             # BaseTool 改造（修改）
  langchain_tools.py       # 辅助函数（不变）

src/business_logic/
  jd/tools/
    read_resume.py         # 改造（使用 ToolContext）
    match_resume_to_job.py # 改造（使用 ToolContext）
    update_resume.py       # 新增
    analyze_resume_skills.py # 新增
    format_resume.py       # 新增
    compare_resumes.py     # 新增
  job/tools/
    __init__.py            # 新增
    search_jobs.py         # 新增
    analyze_jd.py          # 新增
    calculate_job_match.py # 新增
  interview/tools/
    __init__.py            # 新增
    generate_interview_questions.py # 新增
    evaluate_interview_answer.py    # 新增
  common/tools/
    __init__.py            # 新增
    web_search.py          # 新增
    extract_keywords.py    # 新增
```

---

## 五、Agent 集成策略（混合模式）

### 5.1 判断标准

**简单任务 → 直接 LLM：**
- 单轮对话，无需外部数据
- 例如：生成面试题、评估单个答案

**复杂任务 → ReAct + Tools：**
- 需要多步骤、读取/更新数据、工具协作
- 例如：JD 定制简历、岗位推荐

### 5.2 ResumeCustomizerAgent 改造

```python
# 改造后：ReAct + Tools
class ResumeCustomizerAgent:
    def __init__(self, tool_registry: ToolRegistry):
        self.executor = AgentExecutor(
            tools=tool_registry,
            llm=LiteLLMAdapter()
        )

    async def customize(self, resume_id, jd_id, context: ToolContext):
        task = f"为简历 {resume_id} 定制匹配岗位 {jd_id} 的版本"
        result = await self.executor.run(
            task=task,
            context=context,
            available_tools=[
                "read_resume",
                "analyze_jd",
                "match_resume_to_job",
                "analyze_resume_skills",
                "update_resume"
            ]
        )
        return result
```

### 5.3 保持直接 LLM 的 Agent

- InterviewCoachAgent（多轮对话，无需工具）
- 通用问答 Agent（简单查询）

---

## 六、测试策略

### 6.1 分层目标

| 层级 | 当前覆盖率 | 目标 | 优先级 |
|------|-----------|------|--------|
| 工具层（新增） | — | 85%+ | P0 |
| 核心 Runtime | 23-34% | 80%+ | P0 |
| 新功能模块 | 12-18% | 75%+ | P1 |
| 业务服务层 | 28-37% | 70%+ | P2 |
| 数据层 | 27-48% | 75%+ | P2 |

### 6.2 P0 - 核心基础设施（Week 5-6 补齐）

| 模块 | 当前 | 目标 |
|------|------|------|
| LiteLLMAdapter | 27% | 80% |
| AgentExecutor | 23% | 80% |
| ToolRegistry | 32% | 80% |
| MemoryStore | 34% | 75% |

### 6.3 P1 - 新功能模块（Week 3-4 补齐）

| 模块 | 当前 | 目标 |
|------|------|------|
| ReviewReportGenerator | 12% | 75% |
| SessionManager | 18% | 75% |
| InterviewCoachAgent | 15% | 75% |
| JdParserService | 14% | 75% |
| ResumeMatchService | 27% | 75% |

### 6.4 P2 - 业务服务层（Week 5-6 补齐）

| 模块 | 当前 | 目标 |
|------|------|------|
| InterviewService | 37% | 70% |
| ResumeService | 28% | 70% |
| JobService | 37% | 70% |
| UserService | 34% | 70% |
| BaseRepository | 27% | 75% |
| ResumeRepository | 48% | 75% |

### 6.5 测试规范

- 单元测试：pytest + pytest-asyncio，mock 外部依赖
- 每个函数至少 1 个正常用例 + 1 个异常用例
- 集成测试：TestClient + SQLite in-memory
- CI 门禁：PR 必须通过 80% 覆盖率检查

---

## 七、文件变更汇总

### 新增文件

```
src/core/tools/tool_context.py
src/business_logic/jd/tools/update_resume.py
src/business_logic/jd/tools/analyze_resume_skills.py
src/business_logic/jd/tools/format_resume.py
src/business_logic/jd/tools/compare_resumes.py
src/business_logic/job/tools/__init__.py
src/business_logic/job/tools/search_jobs.py
src/business_logic/job/tools/analyze_jd.py
src/business_logic/job/tools/calculate_job_match.py
src/business_logic/interview/tools/__init__.py
src/business_logic/interview/tools/generate_interview_questions.py
src/business_logic/interview/tools/evaluate_interview_answer.py
src/business_logic/common/tools/__init__.py
src/business_logic/common/tools/web_search.py
src/business_logic/common/tools/extract_keywords.py
tests/unit/core/tools/test_tool_context.py
tests/unit/business_logic/tools/（各工具单元测试）
tests/integration/tools/（各工具集成测试）
```

### 修改文件

```
src/core/tools/base_tool.py          # 接入 ToolContext
src/core/runtime/tool_registry.py    # execute() 传入 context
src/business_logic/jd/tools/read_resume.py         # 改造
src/business_logic/jd/tools/match_resume_to_job.py # 改造
src/business_logic/jd/resume_customizer_agent.py   # ReAct 改造
```

---

## 八、验收标准

1. 工具总数 ≥ 13 个，每个工具有单元测试
2. 整体测试覆盖率 ≥ 80%
3. 所有现有测试（435个）继续通过
4. ResumeCustomizerAgent 改造后功能不退化
5. ToolContext 注入后，工具可在测试中使用 mock db
