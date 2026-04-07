# Phase 14 开源基础补全设计

> 日期：2026-04-07 | 状态：草稿

## 决策

| 决策项 | 选择 |
|--------|------|
| LICENSE | MIT |
| CONTRIBUTING.md | 标准（B）— 包含开发环境搭建、代码规范、PR 流程、测试要求 |
| CODE_OF_CONDUCT.md | 新建 |
| SECURITY.md | 新建 — 安全漏洞披露流程 |
| Issue/PR 模板 | 实用集（B）— Bug报告、Feature请求、文档改进、PR 四种 |
| Demo 完善 | 修复 seed_demo + 恢复 E2E 链 |
| README | 技术演示式（C）— 面向技术面试官 |

## 1. 文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `LICENSE` | 新建 | MIT 许可证 |
| `CONTRIBUTING.md` | 新建 | 标准贡献指南 |
| `CODE_OF_CONDUCT.md` | 新建 | 社区行为准则 |
| `SECURITY.md` | 新建 | 安全漏洞披露流程 |
| `.github/ISSUE_TEMPLATE/bug_report.md` | 新建 | Bug 报告模板 |
| `.github/ISSUE_TEMPLATE/feature_request.md` | 新建 | 功能请求模板 |
| `.github/ISSUE_TEMPLATE/docs_improvement.md` | 新建 | 文档改进模板 |
| `.github/PULL_REQUEST_TEMPLATE.md` | 新建 | PR 模板 |
| `tests/integration/test_seed_demo.py` | 修复 | 解决 SQLite schema drift |
| `tests/e2e/test_demo_chain.py` | 恢复 | 完整用户 E2E 流程 |
| `README.md` | 重写 | 技术演示式 |

## 2. 设计原则

- **法律合规**：LICENSE + SECURITY.md 覆盖基本法务要求
- **降低门槛**：CONTRIBUTING.md 让贡献者知道如何上手
- **社区规范**：CODE_OF_CONDUCT 建立行为底线
- **模板效率**：Issue/PR 模板减少沟通成本
- **Demo 稳定**：修复跳过测试，确保 CI 绿

## 3. LICENSE

采用 MIT 许可证，内容取自 https://opensource.org/license/MIT，不做任何修改。

## 4. CONTRIBUTING.md 结构

```
## 开发环境搭建
- 克隆仓库
- Python 环境要求
- 安装依赖（poetry / pip）
- 本地数据库启动（docker-compose）

## 代码规范
- Python: PEP 8
- 前端: ESLint + Prettier
- Commit message: Conventional Commits

## PR 流程
- Fork → Branch → 开发 → 测试 → PR
- PR 需要通过所有测试
- CI 检查项说明

## 测试要求
- 单元测试 + 集成测试必须通过
- 前端需要通过类型检查

## 响应时间预期
- 维护者会在 48h 内回复
```

## 5. CODE_OF_CONDUCT.md

采用 Contributor Covenant 2.1，内容取自 https://www.contributor-covenant.org/version/2/1/code_of_conduct/，不做任何修改。

## 6. SECURITY.md

```
## 支持的版本
说明当前版本的维护状态

## 报告漏洞
- 不要在 GitHub Issue 公开报告
- 发送邮件至 [维护者邮箱]
- 预期响应时间
- 公开披露时间线
```

## 7. Issue 模板说明

| 模板 | 用途 | 关键字段 |
|------|------|----------|
| bug_report.md | Bug 反馈 | 重现步骤、环境信息、预期vs实际 |
| feature_request.md | 功能请求 | 解决的问题、建议方案、替代方案 |
| docs_improvement.md | 文档改进 | 改进建议、相关文件、原因 |

## 8. PR 模板

```
## 描述
一句话总结本次 PR 改了什么

## 变更类型
- [ ] Bug 修复
- [ ] 新功能
- [ ] 文档更新
- [ ] 重构

## 测试
- [ ] 单元测试
- [ ] 集成测试
- [ ] 手动测试（如涉及 UI）

## 相关 Issue
Closes #xxx
```

## 9. test_seed_demo.py 修复策略

**问题**：SQLite 不支持 Alembic migration，schema drift 导致测试跳过。

**修复方案**：
1. 确认跳过原因是否是 PostgreSQL 专属语法（如 `now()` 函数、`interval` 类型）
2. 如果是 Alembic migration 依赖问题，改为直接用 SQLAlchemy 创建表
3. 确保测试在真实 PostgreSQL 环境下通过

## 10. test_demo_chain.py 恢复策略

**覆盖流程**：登录 → 上传简历 → JD 匹配 → 面试对练 → 报告

**技术实现**：Playwright E2E，使用 `tests/e2e/conftest.py` 中的 `api_client` 和 `browser` fixtures

**注意**：如果涉及完整的 AI 对话流，考虑用 mock 替代真实 LLM 调用以确保测试稳定性

## 11. README 重写结构（技术演示式）

```
# AI 实习求职 Agent 系统

[一句话 tagline，不超过一行]

## 解决了什么问题
[2-3句话说明核心价值]

## 技术架构图
[Agent Runtime 全景 ASCII/文本图]

## 核心技术亮点
- AgentExecutor（ReAct Loop）
- ToolRegistry + BaseTool 抽象
- StateMachine 状态管理
- MemoryStore 上下文记忆
- SSE 流式响应

## 快速开始
### 本地开发
[3步命令]
### Docker
[2步命令]

## API 示例
[1-2个 curl/wget 示例，覆盖核心端点]

## 技术栈
后端 | 前端 | 基础设施

## 项目结构
[可选，视长度]
```

面向受众：技术面试官/技术总监，体现工程能力。

## 12. 验证

- 所有新建文件符合规范
- `python -m pytest tests/ -q` 通过
- README 在本地预览正常
