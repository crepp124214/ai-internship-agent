# 基础重构实施计划

## 目标

根据 `internship-design-document.md` 与 `tech-stack.md`，将当前项目从旧式伪 Agent 结构重构为可继续演进的基础版本。

## 当前阶段范围

当前只做基础重构，不做完整最终形态。

本阶段重点：

1. 清理旧结构
2. 收敛架构边界
3. 稳定基础域
4. 为新主线能力预留正确扩展点

## 决策记录（2026-04-06）

| 问题 | 决策 |
|------|------|
| Tracker 清理方式 | 先断开路由/前端入口，保留后端代码，等基础域稳定后再物理删除 |
| 基础域"稳定"验收标准 | 分层依赖方向正确 + 有测试覆盖 + API 契约固定，三项全部满足 |
| 旧 `interview_agent` 处理 | 先重命名/迁移到新目录结构，再逐步改实现，不直接替换 |
| Agent Runtime 本阶段范围 | ✅ 已实现完整功能（LiteLLM Adapter + StateMachine + MemoryStore + ContextBuilder + ToolRegistry + AgentExecutor ReAct 循环） |

---

## 执行顺序

### 1. 文档与规则对齐

- 确认所有规则入口都以 `internship-design-document.md` 和 `tech-stack.md` 为准
- 修正执行层文档，避免与源文档冲突

### 2. Tracker 入口断开（不删后端代码）

- 注释/移除前端 `tracker-page.tsx` 的路由注册
- 注释/移除后端 `src/presentation/api/v1/tracker.py` 的路由注册
- 保留 `src/business_logic/tracker/`、`src/data_access/` 中 tracker 相关文件
- 验证：应用启动正常，Tracker 路由不可访问，其他功能不受影响

### 3. 基础结构收敛

- 检查 `presentation -> business_logic -> data_access` 依赖方向
- 清理 API 层中的业务逻辑
- 清理不符合共享层职责的 `core` 代码

### 4. 基础业务稳定

稳定以下四个域，每个域的验收标准：
- 分层依赖方向正确（无越层调用）
- 有对应单元/集成测试覆盖
- API 契约固定（Schema 稳定，不随意变更）

需稳定的域：
- 用户域
- 简历域
- 岗位域
- 面试域（含旧 `interview_agent` 迁移：先重命名到 `src/business_logic/interview/`，再逐步改实现）

### 5. 新主线预留

- 为 `JD 定制简历` 建立目录结构与空文件（`src/business_logic/jd/`）
- 为 `AI 面试官对练` 建立目录结构与空文件（`src/business_logic/interview/` 扩展）
- 为 Agent Runtime 建立目录结构 — **已升级为完整实现**：LiteLLM Adapter + StateMachine + MemoryStore + ContextBuilder + ToolRegistry + BaseTool + AgentExecutor（ReAct 循环）+ 集成测试
- 本阶段完成 Agent Runtime Phase 1 实现

## 验证要求

每一步都必须带验证，至少包括：

- 文件结构检查
- 关键引用检查
- 对应测试通过
- 文档同步更新

## 完成标准

- 文档入口统一 ✅
- Tracker 路由入口已断开，后端代码保留待后续清理 ✅
- 基础分层结构清晰，无越层依赖 ✅
- 四个基础域满足三项验收标准 ✅
- 新主线目录结构已预留 ✅
- **Agent Runtime Phase 1 完整实现 ✅**（LiteLLM + StateMachine + MemoryStore + ContextBuilder + ToolRegistry + AgentExecutor ReAct 循环，37 tests passed）
