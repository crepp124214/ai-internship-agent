# Progress

## 当前阶段

- 基础重构 ✅ 已完成
- **Agent Runtime Phase 1 ✅ 已完成（2026-04-07）**

## 已完成

- 建立 `memory-bank/` 执行层目录
- 恢复正式源文档入口
- 重写规则层与执行层文档，使其对齐正式设计方案与技术栈文档
- 澄清并固化四项关键决策（见 `implementation-plan.md` 决策记录）

---

## Phase 1：基础重构 ✅ 完成

| Step | 内容 | 状态 |
|------|------|------|
| 1 | Tracker 入口断开（前端路由 + 后端路由注册，保留后端代码） | ✅ |
| 2 | 越层调用修复（auth.py + user/service.py） | ✅ |
| 3 | 四个基础域稳定（用户/简历/岗位/面试） | ✅ |
| 4 | 旧 `interview_agent` 迁移到 `src/business_logic/interview/` | ✅ |
| 5 | 新主线目录预留（jd/、interview/ 扩展、core/runtime/、core/tools/） | ✅ |

**Step 1 完成记录：**
- 前端 `frontend/src/app/router.tsx`：移除 `/tracker` 路由和 `TrackerPage` 导入
- 后端 `src/main.py`：注释掉 tracker router 的 import 和 include_router
- 后端 `src/presentation/api/v1/jobs.py`：更新 `TRACKER_APPLICATIONS_DETAIL` 常量
- 验证：`python -c "from src.main import app"` ✅

---

## Phase 2：Agent Runtime 基础设施 ✅ 完成（2026-04-07）

### 实现清单

| 模块 | 文件 | Commit | 测试 |
|------|------|--------|------|
| StateMachine | `src/core/runtime/state_machine.py` | `097b64d` | 5 passed |
| LiteLLM Adapter | `src/core/llm/litellm_adapter.py` | `8633495` | 3 passed |
| MemoryStore | `src/core/runtime/memory_store.py` | `ad3fccb` | 8 passed |
| ContextBuilder | `src/core/runtime/context_builder.py` | `f98ff9c` | 6 passed |
| ToolRegistry + BaseTool | `src/core/runtime/tool_registry.py` + `src/core/tools/base_tool.py` | `94d4a5a` | 6 passed |
| AgentExecutor (ReAct Loop) | `src/core/runtime/agent_executor.py` | `54e27a2` | 7 passed |
| 集成测试 | `tests/integration/runtime/test_agent_executor_integration.py` | `74340c1` | 2 passed |
| 依赖 | `requirements.txt` (litellm, langchain-core, langchain-community) | `ced834f` | 37 total ✅ |

**Agent Runtime 新增文件：**
```
src/core/llm/litellm_adapter.py          # LiteLLM 统一 adapter
src/core/runtime/state_machine.py         # Agent 执行状态机
src/core/runtime/memory_store.py          # Redis + ChromaDB 记忆存储
src/core/runtime/context_builder.py       # RAG 上下文构建
src/core/runtime/tool_registry.py         # 工具注册表
src/core/runtime/agent_executor.py       # ReAct 执行循环
src/core/tools/base_tool.py              # LangChain BaseTool 封装
src/core/tools/langchain_tools.py         # @tool 装饰器辅助
tests/unit/core/runtime/                  # 各模块单元测试
tests/unit/core/test_litellm_adapter.py  # LiteLLM adapter 测试
tests/integration/runtime/                # 集成测试
```

**设计文档：** `memory-bank/architecture.md`（Agent Runtime 详细设计）

---

## 当前阶段

- Phase 1（基础重构）✅ 完成
- Phase 2（Agent Runtime）✅ 完成
- 下一阶段：JD 定制简历 或 AI 面试官对练 功能开发

## 更新要求

- 每完成一个重要步骤都要更新本文件
- 更新时要说明：
  - 做了什么
  - 影响了哪些文件
  - 做了哪些验证
  - 当前剩余风险是什么
