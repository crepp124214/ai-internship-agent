# Frontend Agent Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 Dashboard 改造为可交互的 Agent 工作台，支持 SSE 流式输出、任务路由、ToolPalette 和 Trace 面板。

**Architecture:** 后端新增 SSE 流式端点 `/api/v1/agent/chat`，前端改造 Dashboard 为 Agent Workspace，复用现有 AgentExecutor。

**Tech Stack:** FastAPI StreamingResponse, SSE, React TanStack Query, Zustand, React Router 6

---

## File Structure

```
src/
├── presentation/api/v1/
│   └── agent.py                     # Create: SSE 流式对话端点
├── business_logic/agent/
│   ├── __init__.py                 # Create
│   └── agent_chat_service.py       # Create: 任务路由服务
frontend/src/
├── pages/
│   ├── dashboard-page.tsx          # Modify: 改造为 Agent Workspace
│   └── components/
│       ├── AgentChatPanel.tsx       # Create: 流式对话面板
│       ├── ToolPalette.tsx          # Create: 工具面板（侧边抽屉）
│       ├── TracePanel.tsx           # Create: ReAct 推理步骤面板
│       └── QuickTaskCard.tsx        # Create: 快捷任务卡片
tests/
├── unit/business_logic/agent/
│   └── test_agent_chat_service.py  # Create
└── integration/
    └── test_agent_chat_sse.py      # Create
```

---

## Task 1: AgentChatService — 任务路由

**Files:**
- Create: `src/business_logic/agent/__init__.py`
- Create: `src/business_logic/agent/agent_chat_service.py`
- Test: `tests/unit/business_logic/agent/test_agent_chat_service.py`

### Steps

- [ ] **Step 1: Create `src/business_logic/agent/__init__.py`**

```python
from .agent_chat_service import AgentChatService

__all__ = ["AgentChatService"]
```

- [ ] **Step 2: Write failing test for `AgentChatService`**

```python
# tests/unit/business_logic/agent/test_agent_chat_service.py
import pytest
from src.business_logic.agent.agent_chat_service import AgentChatService


class TestAgentChatService:
    def setup_method(self):
        self.service = AgentChatService()

    def test_route_to_jd_customizer(self):
        result = self.service.route_task("帮我定制简历")
        assert result == "jd_customizer"

    def test_route_to_interview_coach(self):
        result = self.service.route_task("我想练习面试")
        assert result == "interview_coach"

    def test_route_to_tracker(self):
        result = self.service.route_task("投递建议")
        assert result == "tracker"

    def test_route_to_generic(self):
        result = self.service.route_task("今天天气怎么样")
        assert result == "generic"

    def test_build_context_from_resume_id(self):
        ctx = self.service.build_context(resume_id=1)
        assert ctx["resume_id"] == 1
        assert "task_type" in ctx
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/unit/business_logic/agent/test_agent_chat_service.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 4: Write `AgentChatService` implementation**

```python
# src/business_logic/agent/agent_chat_service.py
"""任务路由服务 — 根据用户任务路由到对应 Agent"""

from dataclasses import dataclass


@dataclass
class TaskContext:
    """任务上下文"""
    resume_id: int | None = None
    jd_id: int | None = None
    session_id: str | None = None
    task_type: str = "generic"


class AgentChatService:
    """根据任务内容路由到对应的 Agent 或处理逻辑"""

    # 路由关键词映射
    ROUTE_KEYWORDS = {
        "jd_customizer": ["简历", "jd", "定制", "匹配度", "岗位"],
        "interview_coach": ["面试", "对练", "练习", "问题", "评分"],
        "tracker": ["投递", "进度", "追踪", "offer", "面试进度"],
    }

    def route_task(self, task: str) -> str:
        """
        根据任务描述返回目标 Agent 标识符。
        """
        task_lower = task.lower()
        for agent, keywords in self.ROUTE_KEYWORDS.items():
            if any(kw in task_lower for kw in keywords):
                return agent
        return "generic"

    def build_context(
        self,
        resume_id: int | None = None,
        jd_id: int | None = None,
        session_id: str | None = None,
    ) -> dict:
        """
        构建任务上下文。
        """
        task_type = "generic"  # 后续根据参数推导
        if resume_id and jd_id:
            task_type = "jd_customizer"
        elif resume_id:
            task_type = "interview_coach"
        return TaskContext(
            resume_id=resume_id,
            jd_id=jd_id,
            session_id=session_id,
            task_type=task_type,
        ).__dict__

    def get_system_prompt(self, task_type: str) -> str:
        """
        根据任务类型返回系统提示词。
        """
        prompts = {
            "jd_customizer": "你是一个简历定制专家，擅长根据岗位分析简历并给出优化建议。",
            "interview_coach": "你是一个资深面试官，擅长评估候选人的技术能力和沟通表达。",
            "tracker": "你是一个求职进度顾问，擅长分析投递状态并给出下一步建议。",
            "generic": "你是一个求职助手，擅长回答各类求职相关问题。",
        }
        return prompts.get(task_type, prompts["generic"])
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/unit/business_logic/agent/test_agent_chat_service.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/business_logic/agent/__init__.py src/business_logic/agent/agent_chat_service.py tests/unit/business_logic/agent/test_agent_chat_service.py
git commit -m "feat(agent): add AgentChatService task routing"
```

---

## Task 2: SSE 流式端点

**Files:**
- Create: `src/presentation/api/v1/agent.py`
- Test: `tests/integration/test_agent_chat_sse.py`

### Steps

- [ ] **Step 1: Write failing integration test**

```python
# tests/integration/test_agent_chat_sse.py
import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app


class TestAgentChatSSE:
    @pytest.fixture
    def anyio_backend(self):
        return "asyncio"

    @pytest.mark.anyio
    async def test_agent_chat_returns_sse_content_type(self):
        """POST /agent/chat 返回 SSE 流"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 先登录获取 token
            login_resp = await client.post(
                "/api/v1/auth/login/",
                json={"username": "testuser", "password": "testpass"},
            )
            if login_resp.status_code == 200:
                token = login_resp.json().get("access_token")
                headers = {"Authorization": f"Bearer {token}"}
                resp = await client.post(
                    "/api/v1/agent/chat",
                    json={"task": "帮我定制简历", "context": {}},
                    headers=headers,
                )
                assert resp.status_code == 200
                assert "text/event-stream" in resp.headers.get("content-type", "")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_agent_chat_sse.py -v`
Expected: FAIL (404 Not Found)

- [ ] **Step 3: Register agent router in main.py**

Read `src/main.py` and add agent router registration after existing routers:
```python
from src.presentation.api.v1 import agent
app.include_router(agent.router, prefix="/api/v1/agent", tags=["Agent"])
```

- [ ] **Step 4: Write `agent.py` with SSE StreamingResponse**

```python
# src/presentation/api/v1/agent.py
"""Agent 流式对话端点"""
import asyncio
import json
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from src.business_logic.agent.agent_chat_service import AgentChatService
from src.core.llm.litellm_adapter import LiteLLMAdapter
from src.core.runtime.memory_store import MemoryStore
from src.core.runtime.tool_registry import ToolRegistry
from src.presentation.api.deps import get_current_user, get_db

router = APIRouter()

# 全局单例
_agent_service = AgentChatService()
_llm = LiteLLMAdapter()


def _build_sse_event(event_type: str, data: dict) -> str:
    return f"data: {json.dumps({'type': event_type, **data})}\n\n"


async def _generate_stream(
    task: str,
    context: dict,
) -> AsyncIterator[str]:
    """
    生成 SSE 流。
    """
    # 路由任务
    task_type = _agent_service.route_task(task)
    system_prompt = _agent_service.get_system_prompt(task_type)

    # 发送 planning 步骤
    yield _build_sse_event("step", {
        "step": "planning",
        "content": f"任务类型：{task_type}，正在分析..."
    })

    # 构建消息
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": task},
    ]

    # 流式调用 LLM
    try:
        async for chunk in _llm.stream_chat(messages=messages):
            if chunk:
                yield _build_sse_event("step", {
                    "step": "final",
                    "content": chunk,
                })
    except Exception as e:
        yield _build_sse_event("error", {"content": str(e)})

    yield _build_sse_event("done", {})


@router.post("/chat")
async def agent_chat(
    task: str,
    context: dict | None = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    SSE 流式 Agent 对话端点。
    """
    if not task or not task.strip():
        raise HTTPException(status_code=400, detail="task is required")

    return StreamingResponse(
        _generate_stream(task.strip(), context or {}),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
```

- [ ] **Step 5: Add `stream_chat` to `LiteLLMAdapter`**

Read `src/core/llm/litellm_adapter.py` and add this method to the `LiteLLMAdapter` class:

```python
async def stream_chat(
    self,
    messages: list[dict],
    tools: list[dict] | None = None,
    model: str | None = None,
    **kwargs,
) -> AsyncIterator[str]:
    """
    流式聊天，返回异步迭代器，每次 yield 一个文本片段。
    litellm 的 stream=True 返回异步生成器，直接 yield ModelResponse chunks。
    """
    params = self._build_litellm_params(messages, tools, **kwargs)
    if model:
        params["model"] = model
    params["stream"] = True
    try:
        response = await acompletion(**params)
    except Exception as exc:
        raise LLMRequestError(f"LiteLLM stream failed: {exc}") from exc

    async for chunk in response:
        content = getattr(chunk.choices[0].delta, "content", None) if hasattr(chunk, "choices") else None
        if content:
            yield content
```

- [ ] **Step 6: Verify module loads**

Run: `python -c "from src.presentation.api.v1.agent import router; print('OK')"`
Expected: OK

- [ ] **Step 7: Run integration test**

Run: `pytest tests/integration/test_agent_chat_sse.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add src/presentation/api/v1/agent.py src/core/llm/litellm_adapter.py src/main.py tests/integration/test_agent_chat_sse.py
git commit -m "feat(api): add SSE streaming agent chat endpoint"
```

---

## Task 3: AgentChatPanel 组件

**Files:**
- Create: `frontend/src/pages/components/AgentChatPanel.tsx`

### Steps

- [ ] **Step 1: Write `AgentChatPanel.tsx`**

```tsx
// frontend/src/pages/components/AgentChatPanel.tsx
import { useState, useRef, useEffect } from 'react'
import { api } from '../../lib/api'
import { useAuth } from '../../auth/use-auth'

interface Message {
  role: 'user' | 'ai'
  content: string
}

interface AgentChatPanelProps {
  initialTask?: string
}

export function AgentChatPanel({ initialTask }: AgentChatPanelProps) {
  const { token } = useAuth()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState(initialTask || '')
  const [streaming, setStreaming] = useState(false)
  const [currentAiContent, setCurrentAiContent] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, currentAiContent])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || streaming) return

    const userMessage = input.trim()
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setInput('')
    setStreaming(true)
    setCurrentAiContent('')

    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/agent/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ task: userMessage, context: {} }),
      })

      if (!response.ok || !response.body) {
        throw new Error('Stream failed')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let done = false

      while (!done) {
        const { value, done: doneReading } = await reader.read()
        done = doneReading
        if (value) {
          const chunk = decoder.decode(value, { stream: !doneReading })
          // SSE 解析
          const lines = chunk.split('\n')
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const event = JSON.parse(line.slice(6))
                if (event.type === 'step' && event.step === 'final') {
                  setCurrentAiContent(prev => prev + event.content)
                } else if (event.type === 'done') {
                  // 流结束
                }
              } catch {
                // 忽略解析错误
              }
            }
          }
        }
      }

      // 合并 AI 消息
      if (currentAiContent) {
        setMessages(prev => [...prev, { role: 'ai', content: currentAiContent }])
      }
      setCurrentAiContent('')
    } catch (err) {
      console.error('Stream error:', err)
      setMessages(prev => [...prev, { role: 'ai', content: '抱歉，发生了错误，请稍后重试。' }])
    } finally {
      setStreaming(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto space-y-4 p-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm ${
                msg.role === 'user'
                  ? 'bg-[var(--color-accent)] text-white rounded-br-md'
                  : 'bg-[var(--color-surface)] text-[var(--color-ink)] rounded-bl-md'
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.content}</p>
            </div>
          </div>
        ))}
        {/* 流式输出中 */}
        {streaming && currentAiContent && (
          <div className="flex justify-start">
            <div className="bg-[var(--color-surface)] text-[var(--color-ink)] rounded-2xl rounded-bl-md px-4 py-3 text-sm max-w-[80%]">
              <p className="whitespace-pre-wrap">{currentAiContent}<span className="animate-pulse">█</span></p>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* 输入框 */}
      <form onSubmit={handleSubmit} className="border-t border-[var(--color-stroke)] p-4">
        <div className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="输入你的求职问题..."
            disabled={streaming}
            className="flex-1 rounded-full border border-[var(--color-stroke)] bg-white px-5 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)] disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={streaming || !input.trim()}
            className="rounded-full bg-[var(--color-accent)] px-6 py-3 text-sm font-medium text-white transition hover:opacity-90 disabled:opacity-50"
          >
            发送
          </button>
        </div>
      </form>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/components/AgentChatPanel.tsx
git commit -m "feat(frontend): add AgentChatPanel with SSE streaming"
```

---

## Task 4: ToolPalette 组件

**Files:**
- Create: `frontend/src/pages/components/ToolPalette.tsx`

### Steps

- [ ] **Step 1: Write `ToolPalette.tsx`**

```tsx
// frontend/src/pages/components/ToolPalette.tsx
import { useState } from 'react'

interface Tool {
  name: string
  description: string
  category: 'resume' | 'job' | 'interview' | 'generic'
}

const TOOLS: Tool[] = [
  { name: 'read_resume', description: '读取简历内容', category: 'resume' },
  { name: 'jd_parser', description: '解析 JD 关键词', category: 'job' },
  { name: 'match_resume_to_job', description: '简历与岗位匹配分析', category: 'job' },
  { name: 'generate_interview_questions', description: '生成面试问题', category: 'interview' },
  { name: 'evaluate_answer', description: '评估回答质量', category: 'interview' },
]

interface ToolPaletteProps {
  onInsertTask: (task: string) => void
}

export function ToolPalette({ onInsertTask }: ToolPaletteProps) {
  const [open, setOpen] = useState(false)

  const byCategory = TOOLS.reduce((acc, tool) => {
    if (!acc[tool.category]) acc[tool.category] = []
    acc[tool.category].push(tool)
    return acc
  }, {} as Record<string, Tool[]>)

  const categoryLabels: Record<string, string> = {
    resume: '简历工具',
    job: '岗位工具',
    interview: '面试工具',
    generic: '通用工具',
  }

  return (
    <>
      {/* 切换按钮 */}
      <button
        onClick={() => setOpen(!open)}
        className="fixed right-4 top-24 z-50 rounded-full bg-[var(--color-surface)] p-3 shadow-lg border border-[var(--color-stroke)] hover:bg-[var(--color-panel)] transition"
        title="工具面板"
      >
        <svg className="w-5 h-5 text-[var(--color-ink)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h7" />
        </svg>
      </button>

      {/* 抽屉 */}
      {open && (
        <div className="fixed right-4 top-32 z-50 w-72 rounded-2xl bg-white shadow-xl border border-[var(--color-stroke)] p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-[var(--color-ink)]">工具面板</h3>
            <button onClick={() => setOpen(false)} className="text-[var(--color-muted)] hover:text-[var(--color-ink)]">
              ✕
            </button>
          </div>
          <div className="space-y-4">
            {Object.entries(byCategory).map(([cat, tools]) => (
              <div key={cat}>
                <p className="text-xs font-medium text-[var(--color-muted)] uppercase tracking-wider mb-2">
                  {categoryLabels[cat] || cat}
                </p>
                <div className="space-y-2">
                  {tools.map(tool => (
                    <button
                      key={tool.name}
                      onClick={() => {
                        onInsertTask(`使用 ${tool.name} 工具：${tool.description}`)
                        setOpen(false)
                      }}
                      className="w-full text-left rounded-xl border border-[var(--color-stroke)] bg-[var(--color-panel)] px-3 py-2 text-sm hover:border-[var(--color-accent)] hover:bg-white transition"
                    >
                      <p className="font-medium text-[var(--color-ink)]">{tool.name}</p>
                      <p className="text-xs text-[var(--color-muted)]">{tool.description}</p>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/components/ToolPalette.tsx
git commit -m "feat(frontend): add ToolPalette component"
```

---

## Task 5: TracePanel 组件

**Files:**
- Create: `frontend/src/pages/components/TracePanel.tsx`

### Steps

- [ ] **Step 1: Write `TracePanel.tsx`**

```tsx
// frontend/src/pages/components/TracePanel.tsx
import { useState } from 'react'

interface TraceStep {
  step: 'planning' | 'tool_call' | 'observation' | 'final'
  content: string
}

interface TracePanelProps {
  steps: TraceStep[]
  open: boolean
  onToggle: () => void
}

const STEP_COLORS: Record<string, string> = {
  planning: 'text-blue-600',
  tool_call: 'text-purple-600',
  observation: 'text-green-600',
  final: 'text-[var(--color-ink)]',
}

const STEP_LABELS: Record<string, string> = {
  planning: '计划',
  tool_call: '工具',
  observation: '观察',
  final: '输出',
}

export function TracePanel({ steps, open, onToggle }: TracePanelProps) {
  return (
    <div className="border-t border-[var(--color-stroke)]">
      {/* 折叠头部 */}
      <button
        onClick={onToggle}
        className="flex w-full items-center justify-between px-4 py-2 text-xs font-medium text-[var(--color-muted)] hover:bg-[var(--color-panel)] transition"
      >
        <span>推理过程 Trace ({steps.length} 步)</span>
        <span>{open ? '▼' : '▲'}</span>
      </button>

      {/* 折叠内容 */}
      {open && (
        <div className="max-h-48 overflow-y-auto bg-[var(--color-canvas)] px-4 pb-3">
          {steps.length === 0 ? (
            <p className="py-2 text-xs text-[var(--color-muted)]">暂无推理步骤</p>
          ) : (
            <div className="space-y-1">
              {steps.map((s, i) => (
                <div key={i} className="flex gap-2 text-xs py-1">
                  <span className={`font-semibold ${STEP_COLORS[s.step] || 'text-gray-600'}`}>
                    [{STEP_LABELS[s.step] || s.step}]
                  </span>
                  <span className="text-[var(--color-ink)] whitespace-pre-wrap">{s.content}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/components/TracePanel.tsx
git commit -m "feat(frontend): add TracePanel component"
```

---

## Task 6: QuickTaskCard 组件

**Files:**
- Create: `frontend/src/pages/components/QuickTaskCard.tsx`

### Steps

- [ ] **Step 1: Write `QuickTaskCard.tsx`**

```tsx
// frontend/src/pages/components/QuickTaskCard.tsx
interface QuickTaskCardProps {
  title: string
  description: string
  icon: string
  onClick: () => void
}

export function QuickTaskCard({ title, description, icon, onClick }: QuickTaskCardProps) {
  return (
    <button
      onClick={onClick}
      className="group text-left rounded-2xl border border-[var(--color-stroke)] bg-[var(--color-panel)] p-4 transition hover:border-[var(--color-accent)] hover:bg-white hover:shadow-md"
    >
      <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--color-accent)]/10 text-xl">
        {icon}
      </div>
      <p className="mb-1 text-sm font-semibold text-[var(--color-ink)] group-hover:text-[var(--color-accent)]">
        {title}
      </p>
      <p className="text-xs text-[var(--color-muted)]">{description}</p>
    </button>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/components/QuickTaskCard.tsx
git commit -m "feat(frontend): add QuickTaskCard component"
```

---

## Task 7: Dashboard 改造

**Files:**
- Modify: `frontend/src/pages/dashboard-page.tsx`

### Steps

- [ ] **Step 1: Read existing dashboard-page.tsx**

- [ ] **Step 2: Replace with Agent Workspace layout**

Replace the entire `DashboardPage` component with:

```tsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AgentChatPanel } from './components/AgentChatPanel'
import { ToolPalette } from './components/ToolPalette'
import { TracePanel } from './components/TracePanel'
import { QuickTaskCard } from './components/QuickTaskCard'

interface TraceStep {
  step: 'planning' | 'tool_call' | 'observation' | 'final'
  content: string
}

const QUICK_TASKS = [
  {
    title: 'JD 定制简历',
    description: '根据岗位定制优化简历',
    icon: '📄',
    task: '帮我根据这个岗位定制简历',
  },
  {
    title: '面试对练',
    description: 'AI 面试官多轮练习',
    icon: '🎤',
    task: '我想进行面试练习',
  },
  {
    title: '岗位推荐',
    description: '根据简历推荐合适岗位',
    icon: '💼',
    task: '帮我推荐一些合适的岗位',
  },
  {
    title: '投递建议',
    description: '分析投递进度与下一步',
    icon: '📋',
    task: '给我的投递一些建议',
  },
]

export function DashboardPage() {
  const navigate = useNavigate()
  const [selectedTask, setSelectedTask] = useState<string | null>(null)
  const [traceSteps, setTraceSteps] = useState<TraceStep[]>([])
  const [traceOpen, setTraceOpen] = useState(false)

  const handleQuickTask = (task: string) => {
    setSelectedTask(task)
  }

  const handleBackToDashboard = () => {
    setSelectedTask(null)
    setTraceSteps([])
  }

  // Agent Workspace 模式
  if (selectedTask) {
    return (
      <div className="flex h-[calc(100vh-8rem)] flex-col rounded-3xl border border-[var(--color-stroke)] bg-white shadow-sm">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[var(--color-stroke)] px-5 py-3">
          <div className="flex items-center gap-3">
            <button
              onClick={handleBackToDashboard}
              className="rounded-lg border border-[var(--color-stroke)] px-3 py-1.5 text-sm hover:bg-[var(--color-panel)] transition"
            >
              ← 返回
            </button>
            <h2 className="text-sm font-semibold text-[var(--color-ink)]">AI 求职助手</h2>
          </div>
          <button
            onClick={() => setTraceOpen(!traceOpen)}
            className={`rounded-lg border px-3 py-1.5 text-xs transition ${
              traceOpen ? 'border-[var(--color-accent)] bg-[var(--color-accent)]/10 text-[var(--color-accent)]' : 'border-[var(--color-stroke)] text-[var(--color-muted)] hover:bg-[var(--color-panel)]'
            }`}
          >
            Trace {traceSteps.length > 0 ? `(${traceSteps.length})` : ''}
          </button>
        </div>

        {/* Trace Panel */}
        <TracePanel
          steps={traceSteps}
          open={traceOpen}
          onToggle={() => setTraceOpen(!traceOpen)}
        />

        {/* Chat Panel */}
        <div className="flex-1 overflow-hidden">
          <AgentChatPanel initialTask={selectedTask} />
        </div>

        {/* Tool Palette */}
        <ToolPalette onInsertTask={(t) => setSelectedTask(t)} />
      </div>
    )
  }

  // 默认仪表盘模式
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.26em] text-[var(--color-muted)]">
            AI 求职工作台
          </p>
          <h1 className="text-2xl font-semibold tracking-[-0.03em] text-[var(--color-ink)]">
            让每一步求职推进都更清楚
          </h1>
        </div>
        <button
          onClick={() => navigate('/resume')}
          className="rounded-full bg-[var(--color-accent)] px-5 py-2.5 text-sm font-medium text-white transition hover:opacity-90"
        >
          进入简历中心
        </button>
      </div>

      {/* 快捷任务区 */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {QUICK_TASKS.map((qt) => (
          <QuickTaskCard
            key={qt.title}
            title={qt.title}
            description={qt.description}
            icon={qt.icon}
            onClick={() => handleQuickTask(qt.task)}
          />
        ))}
      </div>

      {/* 提示区 */}
      <div className="rounded-2xl border border-[var(--color-stroke)] bg-[var(--color-panel)] p-6 text-center">
        <p className="text-sm text-[var(--color-muted)]">
          点击上方快捷任务卡片，或直接输入任何求职问题
        </p>
        <p className="mt-1 text-xs text-[var(--color-muted)]">
          AI 将根据你的上下文自动调用合适的工具处理
        </p>
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/dashboard-page.tsx
git commit -m "feat(frontend): transform dashboard into Agent Workspace"
```

---

## Spec Coverage Check

| Spec Section | Task |
|---|---|
| AgentChatService 任务路由 | Task 1 |
| SSE 流式端点 `/agent/chat` | Task 2 |
| AgentChatPanel 流式对话 | Task 3 |
| ToolPalette 工具面板 | Task 4 |
| TracePanel 推理步骤 | Task 5 |
| QuickTaskCard 快捷任务 | Task 6 |
| Dashboard 改造 | Task 7 |
