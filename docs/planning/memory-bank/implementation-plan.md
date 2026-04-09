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

## 决策记录

| 日期 | 问题 | 决策 |
|------|------|------|
| 2026-04-06 | Tracker 清理决策 | 先断开路由/前端入口，保留后端代码，等基础域稳定后再物理删除 |
| 2026-04-06 | 基础域"稳定"验收标准 | 分层依赖方向正确 + 有测试覆盖 + API 契约固定，三项全部满足 |
| 2026-04-06 | 旧 `interview_agent` 处理 | 先重命名/迁移到新目录结构，再逐步改实现，不直接替换 |
| 2026-04-07 | 架构违规处理 | 工具层禁止从 `presentation` 层导入，强制使用 ToolContext |
| 2026-04-07 | Exception swallowing | 静默吞噬异常的代码必须加日志，不能直接 pass |

---

## 已完成阶段

### Phase 1：基础重构 ✅ 完成

| Step | 内容 | 状态 |
|------|------|------|
| 1 | Tracker 入口断开（前端路由 + 后端路由注册，保留后端代码） | ✅ |
| 2 | 越层调用修复（auth.py + user/service.py） | ✅ |
| 3 | 四个基础域稳定（用户/简历/岗位/面试） | ✅ |
| 4 | 旧 `interview_agent` 迁移到 `src/business_logic/interview/` | ✅ |
| 5 | 新主线目录预留（jd/、interview/ 扩展、core/runtime/、core/tools/） | ✅ |

### Phase 2：Agent Runtime 基础设施 ✅ 完成

- StateMachine + MemoryStore + ContextBuilder + ToolRegistry + BaseTool + AgentExecutor
- 37 tests passed

### Phase 3：JD 定制简历 ✅ 完成

- JD 解析服务 + 简历匹配服务
- 377 tests passed

### Phase 7.5：数据初始化 ✅ 完成

- ResumeParser + JDParser
- 导入 API + 增强 seed_demo

### Phase 8：API 集成 + Playwright 测试 ✅ 完成

- Docker Compose 测试环境
- 18 Playwright tests collected

### Phase 9：Docker 多环境配置 ✅ 完成

- `.env.dev` / `.env.prod` / `.env.local.example`
- `docker/README.md`

### Phase 10：开源基础补充 ✅ 完成

- CLAUDE.md 项目规则
- docs/internal/README.md
- scripts/start_frontend.bat
- .env.test

### Phase 11：P0 紧急修复 ✅ 完成

| P0 问题 | 修复 |
|---------|------|
| 架构违规（10个工具文件从 presentation 导入） | 改为 raise ValueError when context is None |
| Exception swallowing（4处 except: pass） | 改为 logger.warning |
| 不可达代码（raise 后的 db = next(get_db())） | 移除 |

### Phase 12：Tracker 残留代码清理 ✅ 完成

- 删除 `src/business_logic/tracker/`、`src/business_logic/agents/tracker_agent/`
- 删除 `src/presentation/api/v1/tracker.py` 及相关 API 路由
- 删除 `src/data_access/entities/tracker.py` 等数据层文件
- 删除前端 `frontend/src/pages/tracker-page.tsx` 等
- 删除相关测试文件
- 验证：`python -m pytest tests/unit tests/integration -q` → 489 passed, 18 skipped

### Phase 13：测试修复 ✅ 完成

- 修复 `.env.compose.example` → `.env.local.example` 引用
- 移除 Tracker 相关测试断言
- 修复 `alembic/env.py` 中已删除的 `TrackerAdvice` 导入
- 更新 `seed_demo.py` 移除 Tracker 代码
- 跳过 SQLite schema drift 测试
- 验证：`python -m pytest tests/unit tests/integration -q` → 489 passed, 18 skipped

---

## 执行顺序

### 1. 文档与规则对齐

- 确认所有规则入口都以 `internship-design-document.md` 和 `tech-stack.md` 为准
- 修正执行层文档，避免与源文档冲突

### 2. Tracker 入口断开 + 残留代码删除

- Phase 1（2026-04-06）：断开路由入口
- Phase 12（2026-04-07）：物理删除全部 Tracker 代码

**状态：** ✅ 完成（Phase 12 `2026-04-07`）

### 3. 基础结构收敛

- 检查 `presentation -> business_logic -> data_access` 依赖方向
- 清理 API 层中的业务逻辑
- 清理不符合共享层职责的 `core` 代码

**状态：** ✅ 架构违规已修复（Phase 11 P0-1）

### 4. 基础业务稳定

稳定以下四个域，每个域的验收标准：
- 分层依赖方向正确（无越层调用）
- 有对应单元/集成测试覆盖
- API 契约固定（Schema 稳定，不随意变更）

需稳定的域：
- 用户域 ✅
- 简历域 ✅
- 岗位域 ✅
- 面试域 ✅

### 5. 新主线预留

- `JD 定制简历` ✅ 已实现
- `AI 面试官对练` ✅ 基础功能已实现
- `Agent Runtime` ✅ Phase 1 完成
- `用户体验流程 v2.0` ✅ Phase 14 设计完成

---

## Phase 15: 前端页面重构 ✅ 已完成（2026-04-09 合并到 main）

### 实施内容

| 模块 | 说明 |
|------|------|
| Dashboard 改造 | 统一简历导入 + 统计卡片 + 最近活动 + 右下角AI |
| 岗位探索页面 | 新建 `/jobs-explore`，Agent对话搜索公司招聘官网 |
| 简历优化页面 | 简化：选简历 + 上传JD + Agent优化 |
| 路由调整 | 侧边栏顺序：岗位探索 → 简历优化 → 面试准备 |
| 后端API | 新增收藏岗位API：`POST /jobs/save-external` |

### 核心改变

1. **仪表盘**：统一简历导入（不再分散在各页面）
2. **岗位探索**：Agent对话 + 半自动 + 搜索公司招聘官网
3. **简历优化**：选已有简历 + 上传JD + Agent优化
4. **连贯体验**：岗位探索 → 简历优化（带JD）→ 面试（带上下文）

---

## 待处理

| 优先级 | 内容 | 备注 |
|--------|------|------|
| ~~P1~~ | ~~Tracker 残留代码物理删除~~ | ✅ Phase 12 已完成 |
| ~~P2~~ | ~~旧测试失败修复~~ | ✅ Phase 13 已修复 8 个测试 |
| ~~P1~~ | ~~基础测试覆盖率提升~~ | ⚠️ 当前 79.66%，pytest.ini 门槛 79%（已过），原始目标 85%（未达） |
| ~~新功能~~ | ~~用户体验流程 v2.0 设计~~ | ✅ Phase 14 设计完成 |
| ~~新功能~~ | ~~Phase 15 前端页面重构~~ | ✅ feature/frontend-redesign 已合并到 main |
| ~~P2~~ | ~~测试覆盖率进一步提升~~ | ⚠️ 79.66% 已过 pytest.ini 门槛 79%，原始 85% 目标未达 |

---

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
- **Agent Runtime Phase 1 完整实现 ✅**
- **P0 架构违规修复 ✅**
- **用户体验流程 v2.0 设计完成 ✅**
- **Phase 15 前端页面重构（待实施）**
