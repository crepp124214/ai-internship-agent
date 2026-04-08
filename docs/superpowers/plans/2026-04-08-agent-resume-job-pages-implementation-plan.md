# Agent 驱动简历/岗位页面 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将简历和岗位页面改造为 Agent 驱动，提供智能助手面板 + 网络搜索公司招聘官网功能。

**Architecture:** Agent 助手面板（React 组件）通过 SSE 与后端 AssistantService 通信，后端使用 AgentExecutor 的 ReAct 循环执行工具调用。ToolPalette 改为从 `/agent/tools` API 动态获取工具列表。

**Tech Stack:** React + TypeScript + TanStack Query（前端），FastAPI + AgentExecutor（后端），web_search 工具（搜索公司招聘官网）

---

## 文件结构映射

### 后端新建

| 文件 | 职责 |
|------|------|
| `src/business_logic/agent/assistant_service.py` | 助手服务：构建 System Prompt，调用 AgentExecutor |
| `src/presentation/api/v1/assistant.py` | API 端点：POST `/agent/assistant/chat`（SSE 流式）|
| `src/presentation/schemas/assistant.py` | Pydantic 请求/响应 Schema |

### 后端修改

| 文件 | 修改内容 |
|------|----------|
| `src/presentation/api/v1/agent.py` | 新增 GET `/agent/tools` 端点 |
| `src/business_logic/job/tools/search_jobs.py` | 替换为 web_search 调用，返回公司招聘官网 URL |

### 前端新建

| 文件 | 职责 |
|------|------|
| `frontend/src/components/agent/AgentAssistantPanel.tsx` | 助手面板组件（可复用于简历/岗位页面）|
| `frontend/src/hooks/useAgentAssistant.ts` | Hook：管理对话历史、上下文、API 调用 |

### 前端修改

| 文件 | 修改内容 |
|------|----------|
| `frontend/src/pages/resume-page.tsx` | 嵌入 AgentAssistantPanel |
| `frontend/src/pages/jobs-page.tsx` | 嵌入 AgentAssistantPanel |
| `frontend/src/pages/components/ToolPalette.tsx` | 改为从 API 动态获取工具列表 |
| `frontend/src/lib/api.ts` | 新增 `getAgentTools()` API 函数 |

---

## Phase 1: 助手面板基础设施

### Task 1: 后端 — AssistantService

**Files:**
- Create: `src/business_logic/agent/assistant_service.py`
- Test: `tests/unit/business_logic/agent/test_assistant_service.py`

---

- [ ] **Step 1: 创建测试文件**

```python
# tests/unit/business_logic/agent/test_assistant_service.py
import pytest
from src.business_logic.agent.assistant_service import AssistantService

def test_build_system_prompt_for_resume_page():
    service = AssistantService()
    prompt = service.build_system_prompt(page="resume", resource_id=123)
    assert "简历" in prompt
    assert "123" in prompt

def test_build_system_prompt_for_job_page():
    service = AssistantService()
    prompt = service.build_system_prompt(page="job", resource_id=456)
    assert "岗位" in prompt
    assert "456" in prompt

def test_build_context_creates_valid_context():
    service = AssistantService()
    ctx = service.build_context(
        page="resume",
        resource_id=1,
        resource_ids=[1, 2],
        history=[{"role": "user", "content": "hello"}]
    )
    assert ctx["page"] == "resume"
    assert ctx["resource_id"] == 1
    assert len(ctx["history"]) == 1
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/unit/business_logic/agent/test_assistant_service.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: 实现 AssistantService**

```python
# src/business_logic/agent/assistant_service.py
"""助手服务 — Agent 助手面板的后端逻辑"""

from dataclasses import dataclass
from typing import AsyncIterator, Optional

from src.core.llm.litellm_adapter import LiteLLMAdapter
from src.core.runtime.agent_executor import AgentExecutor
from src.core.runtime.context_builder import ContextBuilder
from src.core.runtime.memory_store import MemoryStore
from src.core.runtime.state_machine import StateMachine
from src.core.runtime.tool_registry import ToolRegistry


@dataclass
class AssistantContext:
    """助手上下文"""
    page: str  # "resume" | "job"
    resource_id: Optional[int] = None
    resource_ids: list[int] = None
    history: list[dict] = None


class AssistantService:
    """处理 Agent 助手面板的对话请求"""

    def __init__(self) -> None:
        self._llm = LiteLLMAdapter()
        self._memory = MemoryStore()
        self._state_machine = StateMachine()
        self._context_builder = ContextBuilder(memory=self._memory)
        self._tool_registry = self._build_tool_registry()

    def _build_tool_registry(self) -> ToolRegistry:
        from src.business_logic.jd.tools.read_resume import ReadResumeTool
        from src.business_logic.jd.tools.analyze_resume_skills import AnalyzeResumeSkillsTool
        from src.business_logic.jd.tools.format_resume import FormatResumeTool
        from src.business_logic.job.tools.search_jobs import SearchJobsTool
        from src.business_logic.job.tools.analyze_jd import AnalyzeJDTool
        from src.business_logic.common.tools.web_search import WebSearchTool

        registry = ToolRegistry()
        for tool_cls in [
            ReadResumeTool,
            AnalyzeResumeSkillsTool,
            FormatResumeTool,
            SearchJobsTool,
            AnalyzeJDTool,
            WebSearchTool,
        ]:
            registry.register(tool_cls())
        return registry

    def build_system_prompt(self, page: str, resource_id: Optional[int] = None) -> str:
        """根据页面上下文构建 System Prompt"""
        page_descriptions = {
            "resume": "用户正在查看简历页面。",
            "job": "用户正在查看岗位页面。",
        }
        base = page_descriptions.get(page, "用户正在使用求职助手。")
        if resource_id:
            base += f" 当前选中的资源 ID：{resource_id}。"
        base += "\n你是求职过程中的智能助手，根据用户请求分析简历或岗位，提供专业建议。"
        return base

    def build_context(
        self,
        page: str,
        resource_id: Optional[int] = None,
        resource_ids: Optional[list[int]] = None,
        history: Optional[list[dict]] = None,
    ) -> dict:
        """构建助手上下文"""
        return {
            "page": page,
            "resource_id": resource_id,
            "resource_ids": resource_ids or [],
            "history": history or [],
        }

    async def chat(
        self,
        message: str,
        context: AssistantContext,
    ) -> AsyncIterator[dict]:
        """
        执行对话，流式返回事件。
        事件类型：step, final, done, error
        """
        system_prompt = self.build_system_prompt(context.page, context.resource_id)
        session_id = f"assistant_{context.page}_{context.resource_id or 'none'}"

        executor = AgentExecutor(
            llm=self._llm,
            tools=self._tool_registry,
            memory=self._memory,
            state_machine=self._state_machine,
            context_builder=self._context_builder,
        )

        try:
            async for chunk in executor.execute(
                task=message,
                session_id=session_id,
                system_prompt=system_prompt,
            ):
                if chunk:
                    yield {"type": "step", "content": chunk}
            yield {"type": "done", "content": ""}
        except Exception as exc:
            yield {"type": "error", "content": str(exc)}
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/unit/business_logic/agent/test_assistant_service.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add tests/unit/business_logic/agent/test_assistant_service.py src/business_logic/agent/assistant_service.py
git commit -m "feat(agent): add AssistantService for agent assistant panel"
```

---

### Task 2: 后端 — Pydantic Schema

**Files:**
- Create: `src/presentation/schemas/assistant.py`
- Test: 无独立测试，集成测试覆盖

---

- [ ] **Step 1: 创建 Schema**

```python
# src/presentation/schemas/assistant.py
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AssistantChatRequest(BaseModel):
    """助手面板对话请求"""
    message: str
    context: "AssistantContextSchema"


class AssistantContextSchema(BaseModel):
    """助手上下文"""
    page: str  # "resume" | "job"
    resource_id: Optional[int] = None
    resource_ids: list[int] = []
    history: list[dict] = []

    model_config = ConfigDict(from_attributes=True)
```

- [ ] **Step 2: 提交**

```bash
git add src/presentation/schemas/assistant.py
git commit -m "feat(schemas): add assistant chat schemas"
```

---

### Task 3: 后端 — API 端点

**Files:**
- Create: `src/presentation/api/v1/assistant.py`
- Modify: `src/presentation/api/v1/agent.py`（新增 GET /tools）
- Test: `tests/integration/api/test_assistant_api.py`

---

- [ ] **Step 1: 创建 assistant.py（SSE 流式端点）**

```python
# src/presentation/api/v1/assistant.py
"""Agent 助手面板 API"""
import json
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from src.business_logic.agent.assistant_service import AssistantService, AssistantContext
from src.presentation.api.deps import get_current_user, get_db
from src.presentation.schemas.assistant import AssistantChatRequest

router = APIRouter()
_assistant_service = AssistantService()


def _build_sse_event(event_type: str, data: dict) -> str:
    return f"data: {json.dumps({'type': event_type, **data})}\n\n"


async def _generate_stream(
    message: str,
    page: str,
    resource_id: int | None,
    resource_ids: list[int],
) -> AsyncIterator[str]:
    ctx = AssistantContext(
        page=page,
        resource_id=resource_id,
        resource_ids=resource_ids,
    )
    try:
        async for event in _assistant_service.chat(message, ctx):
            yield _build_sse_event(event["type"], {"content": event["content"]})
    except Exception as exc:
        yield _build_sse_event("error", {"content": str(exc)})


@router.post("/assistant/chat")
async def assistant_chat(
    req: AssistantChatRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Agent 助手面板的 SSE 流式对话端点。
    """
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="message is required")

    return StreamingResponse(
        _generate_stream(
            message=req.message.strip(),
            page=req.context.page,
            resource_id=req.context.resource_id,
            resource_ids=req.context.resource_ids,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
```

- [ ] **Step 2: 修改 agent.py（新增 GET /tools）**

在 `agent.py` 末尾添加：

```python
from src.core.runtime.tool_registry import ToolRegistry

# 全局工具注册表
_global_tool_registry = None

def _get_global_tool_registry() -> ToolRegistry:
    global _global_tool_registry
    if _global_tool_registry is None:
        from src.business_logic.jd.tools.read_resume import ReadResumeTool
        from src.business_logic.jd.tools.analyze_resume_skills import AnalyzeResumeSkillsTool
        from src.business_logic.jd.tools.format_resume import FormatResumeTool
        from src.business_logic.job.tools.search_jobs import SearchJobsTool
        from src.business_logic.job.tools.analyze_jd import AnalyzeJDTool
        from src.business_logic.common.tools.web_search import WebSearchTool

        registry = ToolRegistry()
        for tool_cls in [
            ReadResumeTool,
            AnalyzeResumeSkillsTool,
            FormatResumeTool,
            SearchJobsTool,
            AnalyzeJDTool,
            WebSearchTool,
        ]:
            registry.register(tool_cls())
        _global_tool_registry = registry
    return _global_tool_registry


class ToolInfo(BaseModel):
    name: str
    description: str
    category: str


@router.get("/tools")
async def get_agent_tools():
    """
    返回当前用户可用的 Agent 工具列表。
    """
    registry = _get_global_tool_registry()
    tools = registry.list_tools()
    return {"tools": tools}
```

- [ ] **Step 3: 修改 agent.py（导入 ToolInfo）**

在 `agent.py` 顶部添加：
```python
from pydantic import BaseModel as PydanticBaseModel
```

并添加 ToolInfo 类（如上 Step 2）。

- [ ] **Step 4: 在 main.py 注册路由**

检查 `src/main.py`，确保 `assistant.py` router 被注册：
```python
from src.presentation.api.v1 import auth, resume, jobs, interview, users, agent, assistant
app.include_router(assistant.router, prefix="/api/v1/agent", tags=["Agent"])
```

- [ ] **Step 5: 编写集成测试**

```python
# tests/integration/api/test_assistant_api.py
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_get_agent_tools_returns_list():
    # 需要先登录获取 session
    login_resp = client.post("/api/v1/auth/login", json={"username": "demo", "password": "demo123"})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/v1/agent/tools", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "tools" in data
    assert isinstance(data["tools"], list)
    tool_names = [t["name"] for t in data["tools"]]
    assert "read_resume" in tool_names
    assert "web_search" in tool_names
```

- [ ] **Step 6: 运行测试**

Run: `pytest tests/integration/api/test_assistant_api.py -v`
Expected: PASS

- [ ] **Step 7: 提交**

```bash
git add src/presentation/api/v1/assistant.py src/presentation/api/v1/agent.py src/main.py
git add tests/integration/api/test_assistant_api.py
git commit -m "feat(api): add assistant chat and tools list endpoints"
```

---

## Phase 2: 前端助手面板组件

### Task 4: useAgentAssistant Hook

**Files:**
- Create: `frontend/src/hooks/useAgentAssistant.ts`
- Test: 无独立测试，E2E 测试覆盖

---

- [ ] **Step 1: 创建 Hook**

```typescript
// frontend/src/hooks/useAgentAssistant.ts
import { useState, useCallback, useRef } from 'react'
import { api } from '../lib/api'

export interface AssistantMessage {
  role: 'user' | 'ai' | 'system'
  content: string
}

export interface AssistantContext {
  page: 'resume' | 'job'
  resourceId?: number
  resourceIds?: number[]
}

export function useAgentAssistant() {
  const [messages, setMessages] = useState<AssistantMessage[]>([])
  const [streaming, setStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const sendMessage = useCallback(async (
    message: string,
    context: AssistantContext,
  ) => {
    // 取消之前的请求
    if (abortRef.current) {
      abortRef.current.abort()
    }
    abortRef.current = new AbortController()

    setStreaming(true)
    setError(null)

    // 添加用户消息
    setMessages(prev => [...prev, { role: 'user', content: message }])

    let fullContent = ''

    try {
      const response = await fetch('/api/v1/agent/assistant/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          context: {
            page: context.page,
            resource_id: context.resourceId,
            resource_ids: context.resourceIds || [],
            history: messages.slice(-10).map(m => ({
              role: m.role === 'ai' ? 'assistant' : m.role,
              content: m.content,
            })),
          },
        }),
        signal: abortRef.current.signal,
      })

      if (!response.ok) {
        throw new Error(`请求失败: ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No response body')

      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const event = JSON.parse(line.slice(6))
            if (event.type === 'step') {
              fullContent += event.content
              setMessages(prev => {
                const last = prev[prev.length - 1]
                if (last?.role === 'ai') {
                  return [...prev.slice(0, -1), { role: 'ai', content: fullContent }]
                }
                return [...prev, { role: 'ai', content: fullContent }]
              })
            } else if (event.type === 'error') {
              setError(event.content)
            }
          } catch {}
        }
      }
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        setError((err as Error).message)
      }
    } finally {
      setStreaming(false)
    }
  }, [messages])

  const clearMessages = useCallback(() => {
    setMessages([])
    setError(null)
  }, [])

  return {
    messages,
    streaming,
    error,
    sendMessage,
    clearMessages,
  }
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/hooks/useAgentAssistant.ts
git commit -m "feat(frontend): add useAgentAssistant hook"
```

---

### Task 5: AgentAssistantPanel 组件

**Files:**
- Create: `frontend/src/components/agent/AgentAssistantPanel.tsx`
- Test: 无独立测试，E2E 测试覆盖

---

- [ ] **Step 1: 创建 AgentAssistantPanel 组件**

```tsx
// frontend/src/components/agent/AgentAssistantPanel.tsx
import { useEffect, useRef } from 'react'
import { useAgentAssistant, type AssistantMessage } from '../../hooks/useAgentAssistant'
import { SecondaryButton } from '../page-primitives'

interface QuickAction {
  label: string
  message: string
}

interface AgentAssistantPanelProps {
  page: 'resume' | 'job'
  resourceId?: number
  resourceIds?: number[]
  quickActions?: QuickAction[]
  onResourceChange?: (resourceId: number) => void
}

export function AgentAssistantPanel({
  page,
  resourceId,
  resourceIds,
  quickActions = [],
}: AgentAssistantPanelProps) {
  const { messages, streaming, error, sendMessage, clearMessages } = useAgentAssistant()
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // 页面切换时清空消息
  useEffect(() => {
    clearMessages()
  }, [page, clearMessages])

  function handleSend(message: string) {
    if (!message.trim() || streaming) return
    sendMessage(message, { page, resourceId, resourceIds })
    setInput('')
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    handleSend(input)
  }

  function handleQuickAction(action: QuickAction) {
    handleSend(action.message)
  }

  return (
    <div className="flex flex-col h-full border-l border-[var(--color-border)] bg-[var(--color-surface)]">
      {/* Header */}
      <div className="px-4 py-3 border-b border-[var(--color-border)]">
        <h3 className="text-sm font-semibold text-[var(--color-ink)]">Agent 助手</h3>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
        {messages.length === 0 && !streaming && (
          <div className="text-sm text-[var(--color-muted)]">
            {page === 'resume'
              ? '选中一份简历，我可以帮您分析、解读或给出改进建议。'
              : '我可以帮您搜索公司招聘官网，或分析岗位与简历的匹配度。'}
          </div>
        )}

        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} />
        ))}

        {streaming && (
          <div className="text-sm text-[var(--color-muted)]">
            <span className="animate-pulse">思考中...</span>
          </div>
        )}

        {error && (
          <div className="text-sm text-red-600 bg-red-50 rounded-[22px] px-4 py-3">
            错误：{error}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Actions */}
      {quickActions.length > 0 && messages.length === 0 && (
        <div className="px-4 pb-2 flex flex-wrap gap-2">
          {quickActions.map((action, i) => (
            <SecondaryButton
              key={i}
              onClick={() => handleQuickAction(action)}
              disabled={streaming}
            >
              {action.label}
            </SecondaryButton>
          ))}
        </div>
      )}

      {/* Input */}
      <form onSubmit={handleSubmit} className="px-4 py-3 border-t border-[var(--color-border)]">
        <div className="flex gap-2">
          <textarea
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSend(input)
              }
            }}
            placeholder={page === 'resume' ? '问关于简历的问题...' : '搜索岗位或分析简历...'}
            className="flex-1 resize-none rounded-[22px] border border-[var(--color-border)] px-4 py-2 text-sm focus:outline-none focus:border-[var(--color-primary)]"
            rows={1}
            disabled={streaming}
          />
          <SecondaryButton type="submit" disabled={streaming || !input.trim()}>
            发送
          </SecondaryButton>
        </div>
      </form>
    </div>
  )
}

function MessageBubble({ message }: { message: AssistantMessage }) {
  const isUser = message.role === 'user'
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[85%] rounded-[22px] px-4 py-3 text-sm ${
          isUser
            ? 'bg-[var(--color-primary)] text-white'
            : 'bg-[var(--color-background)] text-[var(--color-ink)] border border-[var(--color-border)]'
        }`}
      >
        {message.content}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: 修复 AgentChatPanel.tsx 中的 fetch URL**

注意：`AgentChatPanel.tsx` 使用了硬编码的 `fetch('/api/v1/agent/chat')`，应改为使用 axios 实例。但这是现有 bug，不在本次范围内。Task 5 只创建新组件。

- [ ] **Step 3: 提交**

```bash
git add frontend/src/components/agent/AgentAssistantPanel.tsx
git commit -m "feat(frontend): add AgentAssistantPanel component"
```

---

## Phase 3: 简历页面改造

### Task 6: 简历页面嵌入 AgentAssistantPanel

**Files:**
- Modify: `frontend/src/pages/resume-page.tsx`
- Test: `tests/e2e/test_resume_page.py`

---

- [ ] **Step 1: 阅读现有 resume-page.tsx 了解结构**

Run: `head -50 frontend/src/pages/resume-page.tsx`

- [ ] **Step 2: 改造简历页面（双栏布局）**

在 `ResumePage` 组件中：
1. 导入 `AgentAssistantPanel`
2. 外层 div 改为双栏布局：`grid grid-cols-[1fr_350px]`
3. 左侧放现有简历列表和详情
4. 右侧放 `AgentAssistantPanel`

```tsx
// 在 resume-page.tsx 中添加

// 在组件 return 的 JSX 中，外层 div 改为：
// <div className="flex h-full">
//   <div className="flex-1"> {/* 左侧现有内容 */} </div>
//   <div className="w-[350px]"> {/* AgentAssistantPanel */} </div>
// </div>

// AgentAssistantPanel 配置：
const resumeQuickActions = [
  { label: '分析简历', message: '请分析我选中的这份简历，指出优势和不足' },
  { label: '我适合什么岗位？', message: '根据我的简历，我适合什么类型的岗位？' },
  { label: '简历有什么问题？', message: '这份简历有什么问题？如何改进？' },
]
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/pages/resume-page.tsx
git commit -m "feat(frontend): embed AgentAssistantPanel in resume page"
```

---

## Phase 4: 岗位页面改造 + 搜索功能

### Task 7: SearchJobsTool — 替换为 web search

**Files:**
- Modify: `src/business_logic/job/tools/search_jobs.py`
- Test: `tests/unit/business_logic/job/tools/test_search_jobs.py`

---

- [ ] **Step 1: 创建测试**

```python
# tests/unit/business_logic/job/tools/test_search_jobs.py
import pytest
from src.business_logic.job.tools.search_jobs import SearchJobsTool
from src.core.tools.tool_context import ToolContext
from src.data_access.database import SessionLocal

@pytest.fixture
def tool():
    return SearchJobsTool()

@pytest.fixture
def context():
    db = SessionLocal()
    return ToolContext(db=db)

def test_search_returns_company_recruitment_urls(tool, context):
    result = tool._execute_sync(
        tool_input={"keyword": "深圳 Python 实习"},
        context=context,
    )
    assert "results" in result
    assert len(result["results"]) > 0
    # 结果应包含公司名称和招聘官网 URL
    for item in result["results"]:
        assert "company" in item
        assert "url" in item
        assert "snippet" in item
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/unit/business_logic/job/tools/test_search_jobs.py -v`
Expected: FAIL — current implementation returns local DB results

- [ ] **Step 3: 重写 SearchJobsTool（调用 web_search，返回公司招聘官网）**

```python
# src/business_logic/job/tools/search_jobs.py
"""
SearchJobsTool — 搜索公司招聘官网

该工具将关键词转换为公司招聘官网搜索，
而不是搜索本地数据库。
"""
from typing import Type

from pydantic import BaseModel

from src.core.tools.base_tool import BaseTool
from src.core.tools.tool_context import ToolContext


class SearchJobsInput(BaseModel):
    """Input schema for search_jobs tool."""
    keyword: str
    location: str = ""  # 如"深圳"
    limit: int = 5


# 常见公司校招官网映射（关键词 → 官网 URL）
KNOWN_COMPANY_RECRUITMENT_PAGES = {
    "字节跳动": "https://jobs.bytedance.com/campus",
    "字节": "https://jobs.bytedance.com/campus",
    "bytedance": "https://jobs.bytedance.com/campus",
    "腾讯": "https://careers.qq.com",
    "腾讯云": "https://careers.qq.com",
    "阿里": "https://campus.aliyun.com",
    "阿里巴巴": "https://campus.aliyun.com",
    "阿里云": "https://campus.aliyun.com",
    "华为": "https://career.huawei.com",
    "shopee": "https://careers.shopee.cn",
    "虾皮": "https://careers.shopee.cn",
    "虾皮信息": "https://careers.shopee.cn",
    "美团": "https://campus.meituan.com",
    "京东": "https://careers.jd.com",
    "快手": "https://careers.kuaishou.cn",
    "百度": "https://talent.baidu.com",
    "网易": "https://campus.163.com",
    "bilibili": "https://job.bilibili.com",
    "b站": "https://job.bilibili.com",
    "小红书": "https://job.xiaohongshu.com",
    "米哈游": "https://careers.mihoyo.com",
    "shein": "https://careers.shein.com",
    "希音": "https://careers.shein.com",
}


class SearchJobsTool(BaseTool):
    """根据关键词搜索公司招聘官网"""

    name: str = "search_jobs"
    description: str = "搜索公司招聘官网 URL，帮助用户找到该公司校园招聘或实习招聘页面"
    args_schema: Type[BaseModel] = SearchJobsInput

    def _execute_sync(
        self,
        tool_input: dict,
        runtime=None,
        context: ToolContext = None,
    ) -> dict:
        from src.business_logic.common.tools.web_search import WebSearchTool

        keyword = tool_input.get("keyword", "")
        location = tool_input.get("location", "")
        limit = tool_input.get("limit", 5)

        if not keyword:
            return {"error": "keyword is required", "results": []}

        if context is None:
            raise ValueError("ToolContext is required")

        # 优先从已知公司映射中查找
        matched_companies = []
        keyword_lower = keyword.lower()
        for company, url in KNOWN_COMPANY_RECRUITMENT_PAGES.items():
            if keyword_lower in company.lower():
                matched_companies.append({
                    "company": company,
                    "url": url,
                    "type": "direct",
                    "snippet": f"{company} 招聘官网，包含校园招聘和实习招聘信息",
                })

        # 如果有关键词匹配的公司，直接返回
        if matched_companies:
            return {
                "keyword": keyword,
                "location": location,
                "count": len(matched_companies),
                "results": matched_companies[:limit],
                "source": "known_companies",
            }

        # 否则使用 web_search 搜索
        search_query = f"{keyword} {location} 2026 校招 实习 招聘官网".strip()
        web_search_tool = WebSearchTool()
        web_results = web_search_tool._execute_sync(
            tool_input={"query": search_query, "limit": limit},
            context=context,
        )

        # 格式化 web_search 结果，提取公司招聘官网
        formatted_results = []
        seen_companies = set()

        for result in web_results.get("results", []):
            url = result.get("url", "")
            title = result.get("title", "")
            snippet = result.get("snippet", "")

            # 提取公司名（从标题中）
            company = self._extract_company_name(title, keyword)

            if company and company not in seen_companies:
                seen_companies.add(company)
                formatted_results.append({
                    "company": company,
                    "url": url,
                    "type": "search",
                    "snippet": snippet[:200] if snippet else "",
                })

        return {
            "keyword": keyword,
            "location": location,
            "count": len(formatted_results),
            "results": formatted_results[:limit],
            "source": "web_search",
        }

    def _extract_company_name(self, title: str, keyword: str) -> str:
        """从搜索结果标题中提取公司名"""
        # 常见模式：字节跳动2026校招官网 -> 字节跳动
        import re
        # 尝试从已知的公司名列表中匹配
        for company in KNOWN_COMPANY_RECRUITMENT_PAGES.keys():
            if company in title:
                return company
        # 尝试提取第一个词作为公司名
        match = re.match(r'^([^\s]+)', title)
        if match:
            return match.group(1)
        return keyword
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/unit/business_logic/job/tools/test_search_jobs.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/business_logic/job/tools/search_jobs.py tests/unit/business_logic/job/tools/test_search_jobs.py
git commit -m "feat(job): rewrite SearchJobsTool to return company recruitment URLs via web search"
```

---

### Task 8: 岗位页面嵌入 AgentAssistantPanel

**Files:**
- Modify: `frontend/src/pages/jobs-page.tsx`
- Test: `tests/e2e/test_jobs_page.py`

---

- [ ] **Step 1: 阅读现有 jobs-page.tsx 了解结构**

Run: `head -50 frontend/src/pages/jobs-page.tsx`

- [ ] **Step 2: 改造岗位页面（双栏布局）**

在 `JobsPage` 组件中：
1. 导入 `AgentAssistantPanel`
2. 外层 div 改为双栏布局
3. 左侧放现有岗位列表
4. 右侧放 `AgentAssistantPanel`

```tsx
// AgentAssistantPanel 配置：
const jobQuickActions = [
  { label: '🔍 搜索岗位', message: '帮我搜索公司招聘官网' },
  { label: '分析 JD', message: '请分析这个岗位的 JD 要求' },
  { label: '与简历匹配', message: '这个岗位和我的简历匹配吗？' },
]
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/pages/jobs-page.tsx
git commit -m "feat(frontend): embed AgentAssistantPanel in jobs page"
```

---

## Phase 5: ToolPalette 动态化

### Task 9: ToolPalette 改为从 API 获取工具列表

**Files:**
- Modify: `frontend/src/pages/components/ToolPalette.tsx`
- Modify: `frontend/src/lib/api.ts`（新增 `getAgentTools`）

---

- [ ] **Step 1: 在 api.ts 添加 getAgentTools**

```typescript
// frontend/src/lib/api.ts 添加

export interface AgentTool {
  name: string
  description: string
  category: string
}

export async function getAgentTools(): Promise<AgentTool[]> {
  const response = await api.get<{ tools: AgentTool[] }>('/agent/tools/')
  return response.data.tools
}
```

- [ ] **Step 2: 修改 ToolPalette.tsx 使用 API 获取工具**

在 `ToolPalette` 组件中：
1. 使用 TanStack Query 的 `useQuery` 调用 `getAgentTools()`
2. 移除硬编码的 `TOOLS` 数组
3. 工具按 category 分组展示

- [ ] **Step 3: 提交**

```bash
git add frontend/src/lib/api.ts frontend/src/pages/components/ToolPalette.tsx
git commit -m "feat(frontend): make ToolPalette fetch tools from API dynamically"
```

---

## 验证清单

| 验证项 | 方法 |
|--------|------|
| 后端 API `/agent/assistant/chat` 流式响应正常 | `curl` 测试 |
| 后端 API `/agent/tools` 返回工具列表 | `curl` 测试 |
| `SearchJobsTool` 返回公司招聘官网 URL | pytest 测试 |
| 简历页面助手面板正常显示和分析 | Playwright E2E |
| 岗位页面助手面板搜索功能正常 | Playwright E2E |
| 单元+集成测试全部通过 | `pytest -q` |
| 覆盖率不低于当前 80% | coverage report |

---

## 实现顺序

1. Task 1 → Task 2 → Task 3（Phase 1 后端）
2. Task 4 → Task 5（Phase 2 前端）
3. Task 6（Phase 3 简历页面）
4. Task 7 → Task 8（Phase 4 岗位页面）
5. Task 9（Phase 5 ToolPalette）
