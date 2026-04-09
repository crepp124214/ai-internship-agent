# Release Candidate Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将当前已合并到 `main` 的 AI 实习求职 Agent 系统收口到“可正式交付”的 Release Candidate 状态，覆盖质量验证、交付文档、试用安全性、作品集包装四个工作包。

**Architecture:** 本阶段不新增主功能，不改产品主链路，只围绕现有实现做封板。所有工作以“证明可交付”为中心，优先补齐关键链路验证、统一文档口径、处理试用级风险，并沉淀可展示材料。

**Tech Stack:** FastAPI, SQLAlchemy, React 18, TypeScript, Vite, pytest, Playwright, Docker Compose, Markdown docs

---

## Scope And Boundaries

- 只处理交付封板，不新增主功能。
- 允许修复阻断交付的 bug、类型问题、测试问题、文档不一致。
- 不做大规模重构，不改变既有页面结构和核心交互。
- 交付目标同时面向“小范围真实试用”和“招聘作品集展示”。

## File Structure

### Existing files likely to change

- `docs/planning/memory-bank/progress.md`
  - 记录封板阶段完成情况、验证结果、残余风险
- `docs/planning/memory-bank/implementation-plan.md`
  - 将旧的“Phase 15 待实施”口径收敛到当前状态
- `docs/planning/memory-bank/architecture.md`
  - 同步 Phase 14/15 落地后的页面、数据流、收口状态
- `README.md`
  - 对外入口文档，面向试用者和面试官
- `docker/README.md`
  - Docker 启动、环境变量、demo 体验说明
- `frontend/src/lib/api.ts`
  - 如交付过程中发现 API 类型或错误处理缺口，可在此做最小修补
- `frontend/src/pages/**`
  - 只允许修复阻断交付的问题，例如空状态、错误态、无效参数
- `src/presentation/api/v1/**`
  - 只允许修复交付阻断类问题，例如接口响应契约或 demo 兼容性
- `tests/**`
  - 为主链路、回归、覆盖率补充测试

### New files to create

- `docs/release/release-candidate-checklist.md`
  - 交付前人工验收清单
- `docs/release/known-issues.md`
  - 已知问题、影响范围、交付决策
- `docs/release/demo-script.md`
  - 3-5 分钟标准演示路径
- `docs/release/portfolio-summary.md`
  - 作品集摘要，突出价值、取舍、技术亮点

## Delivery Standard

交付完成需要同时满足：

1. 主链路可跑通并有证据
2. 自动化测试通过并达到最低覆盖率目标
3. 文档口径一致，不存在“已完成/待实施”冲突
4. demo 环境能启动，关键体验不依赖人工解释
5. 已知风险被记录，并明确是否接受带风险交付

## Task 1: Build The Release Acceptance Checklist

**Files:**
- Create: `docs/release/release-candidate-checklist.md`
- Modify: `docs/planning/memory-bank/progress.md`
- Reference: `README.md`

- [ ] **Step 1: 列出交付验收主链路**

在 `docs/release/release-candidate-checklist.md` 中写出 5 条必须通过的交付链路：

```md
## 必过链路

1. 登录 demo 账号并进入系统首页
2. 在岗位探索页完成岗位导入或创建，并保存岗位
3. 从岗位上下文进入简历优化并完成一次 JD 定向优化
4. 从简历优化进入面试准备并开始一次面试会话
5. 在设置中心查看面试记录并校验 Agent 配置页面可用
```

- [ ] **Step 2: 为每条链路补充验收字段**

为每条链路写出固定字段：

```md
- 前置条件
- 操作步骤
- 预期结果
- 实际结果
- 负责人
- 验收日期
```

- [ ] **Step 3: 将封板阶段写入进度文档**

在 `docs/planning/memory-bank/progress.md` 顶部补充封板阶段条目，例如：

```md
- Release Candidate 封板：进行中（质量验证 / 文档统一 / 试用安全性 / 作品集包装）
```

- [ ] **Step 4: 自检文档格式**

Run: `Get-Content docs\release\release-candidate-checklist.md`
Expected: 验收清单包含 5 条链路和统一字段

- [ ] **Step 5: Commit**

```bash
git add docs/release/release-candidate-checklist.md docs/planning/memory-bank/progress.md
git commit -m "docs: add release candidate acceptance checklist"
```

## Task 2: Raise Coverage To The Minimum Delivery Target

**Files:**
- Modify: `tests/unit/**`
- Modify: `tests/integration/**`
- Modify: `tests/e2e/**`
- Reference: `pytest.ini`
- Reference: `coverage.xml`

- [ ] **Step 1: 识别覆盖率最低且影响交付的模块**

运行覆盖率报告并记录候选模块。

Run: `python -m pytest tests/unit tests/integration -p no:cacheprovider --cov=src --cov-report=term-missing`
Expected: 输出缺失覆盖率的模块清单，优先关注主链路相关模块

- [ ] **Step 2: 选定最小补测范围**

只选 3 类模块补测：

```text
1. 岗位探索与保存链路
2. 简历优化链路
3. 面试记录查看 / 配置读取链路
```

- [ ] **Step 3: 为第一个薄弱模块写失败测试**

示例骨架：

```python
def test_save_external_job_persists_required_fields(client, auth_headers):
    response = client.post(
        "/api/v1/jobs/save-external",
        headers=auth_headers,
        json={
            "title": "Backend Intern",
            "company": "Example",
            "source_url": "https://example.com/jobs/1",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "Backend Intern"
```

- [ ] **Step 4: 运行单测确认失败原因正确**

Run: `python -m pytest tests/integration/api/test_jobs_api.py -k save_external -v -p no:cacheprovider`
Expected: 如果行为缺失则失败；如果已有行为则进入下一薄弱模块

- [ ] **Step 5: 写最小实现或补充现有断言**

仅实现交付阻断缺口，禁止顺手扩功能。

- [ ] **Step 6: 针对简历优化和面试记录重复 TDD**

示例关注点：

```text
- resumeApi.customizeForJd 响应契约
- settings interviews 页面依赖的后端接口
- coach report 数据缺失时的回退行为
```

- [ ] **Step 7: 跑完整验证并检查覆盖率**

Run: `python -m pytest tests/unit tests/integration -p no:cacheprovider`
Expected: 全部通过

Run: `python -m pytest tests/unit tests/integration -p no:cacheprovider --cov=src --cov-report=term`
Expected: 总覆盖率 >= 80%

- [ ] **Step 8: Commit**

```bash
git add tests src frontend/src/lib/api.ts frontend/src/pages
git commit -m "test: raise release candidate coverage to target"
```

## Task 3: Run End-To-End Smoke Validation

**Files:**
- Modify: `tests/e2e/**`
- Create: `docs/release/known-issues.md`
- Modify: `docs/planning/memory-bank/progress.md`

- [ ] **Step 1: 固化最小冒烟用例列表**

只保留交付相关用例：

```text
- 登录与首页加载
- 岗位探索保存岗位
- 简历优化主流程
- 面试准备启动会话
- 设置中心查看面试记录
```

- [ ] **Step 2: 为缺失链路补最小 e2e 或 integration 测试**

优先已有测试目录与命名风格，避免新建大而全框架。

- [ ] **Step 3: 运行关键冒烟集**

Run: `python -m pytest tests/e2e -p no:cacheprovider`
Expected: 关键 e2e 用例通过；若环境限制导致无法全跑，记录阻塞原因

- [ ] **Step 4: 记录已知问题**

在 `docs/release/known-issues.md` 中使用固定模板：

```md
## Issue
- 描述：
- 影响范围：
- 是否阻断交付：
- 临时规避方案：
- 后续修复建议：
```

- [ ] **Step 5: 更新 progress.md 中的验证结果**

写明：

```md
- 跑了哪些自动化验证
- 哪些链路人工确认通过
- 还剩哪些已接受风险
```

- [ ] **Step 6: Commit**

```bash
git add tests/e2e docs/release/known-issues.md docs/planning/memory-bank/progress.md
git commit -m "test: add release smoke validation and issue log"
```

## Task 4: Unify Public Delivery Documentation

**Files:**
- Modify: `README.md`
- Modify: `docker/README.md`
- Modify: `docs/planning/memory-bank/implementation-plan.md`
- Modify: `docs/planning/memory-bank/architecture.md`

- [ ] **Step 1: 修正 implementation-plan 旧口径**

将 `Phase 15 待实施` 改为与当前进度一致的已完成状态，并补充封板阶段位置。

- [ ] **Step 2: 更新 README 的对外叙事**

README 顶部应明确：

```md
- 产品定位
- 核心功能
- 当前完成状态
- 快速启动方式
- demo 体验路径
```

- [ ] **Step 3: 更新 Docker 说明**

确保 `docker/README.md` 讲清：

```md
- 如何启动
- 需要哪些 env
- 默认 demo 账号
- 哪些能力依赖真实 LLM
- mock 模式下能体验什么
```

- [ ] **Step 4: 更新 architecture.md**

补齐当前页面架构、Phase 14/15 完成状态、主链路数据流、封板策略。

- [ ] **Step 5: 逐份自检避免冲突**

Run: `rg "待实施|已完成|Phase 15|Phase 14" README.md docs/planning/memory-bank docs/release`
Expected: 不存在同一事项同时被描述为“已完成”和“待实施”

- [ ] **Step 6: Commit**

```bash
git add README.md docker/README.md docs/planning/memory-bank/implementation-plan.md docs/planning/memory-bank/architecture.md
git commit -m "docs: align delivery documentation for release candidate"
```

## Task 5: Add Trial-Safety Guardrails

**Files:**
- Modify: `.env.local.example`
- Modify: `.env.dev`
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/pages/settings/**`
- Modify: `src/presentation/api/v1/**`

- [ ] **Step 1: 审查默认配置的试用安全性**

重点检查：

```text
- 示例 env 是否误导用户填真实密钥
- mock 模式是否可直接体验
- demo 环境是否需要隐藏前提
```

- [ ] **Step 2: 为配置缺失场景写失败测试**

示例：

```python
def test_user_llm_config_returns_clear_error_when_provider_missing(client, auth_headers):
    response = client.post("/api/v1/user-llm-config", headers=auth_headers, json={})
    assert response.status_code in {400, 422}
```

- [ ] **Step 3: 修复静默失败或模糊错误提示**

前后端统一要求：

```text
- 请求失败时能看到明确错误信息
- 空数据时有空状态
- mock / demo / real provider 的差异有明确提示
```

- [ ] **Step 4: 手动验证 3 个失败场景**

```text
1. 未配置真实 LLM
2. 面试记录为空
3. 外部岗位数据不完整
```

- [ ] **Step 5: 将接受的残余风险写入 known-issues**

只记录接受带着交付的问题，不记录纯愿望项。

- [ ] **Step 6: Commit**

```bash
git add .env.local.example .env.dev frontend/src/lib/api.ts frontend/src/pages/settings src/presentation/api/v1 docs/release/known-issues.md
git commit -m "fix: add trial-safety guardrails for release candidate"
```

## Task 6: Prepare Portfolio And Demo Materials

**Files:**
- Create: `docs/release/demo-script.md`
- Create: `docs/release/portfolio-summary.md`
- Reference: `dashboard-ux.png`
- Reference: `jobs-ux.png`
- Reference: `resume-ux.png`
- Reference: `interview-ux.png`

- [ ] **Step 1: 写 3-5 分钟标准演示脚本**

在 `docs/release/demo-script.md` 中固定结构：

```md
1. 开场：用户痛点与产品定位
2. 登录与仪表盘
3. 岗位探索与收藏
4. 简历优化
5. 面试准备
6. 设置中心与 Agent 配置
7. 架构亮点与收尾
```

- [ ] **Step 2: 写作品集摘要**

在 `docs/release/portfolio-summary.md` 中覆盖：

```md
- 背景问题
- 解决方案
- 核心功能
- 架构亮点
- 技术栈
- 我的关键工程判断
- 已知边界与后续方向
```

- [ ] **Step 3: 绑定现有截图与待补截图**

在文档中记录每个页面对应的截图资源名，缺什么再补什么。

- [ ] **Step 4: 自检叙事一致性**

确保文档主线统一为：

```text
岗位探索 -> 简历优化 -> 面试准备
```

并明确强调：

```text
- 从伪 Agent 到 Agent Runtime 的重构
- 砍掉 Tracker 的取舍
- 为什么收敛成现在这条主流程
```

- [ ] **Step 5: Commit**

```bash
git add docs/release/demo-script.md docs/release/portfolio-summary.md
git commit -m "docs: add release demo and portfolio materials"
```

## Task 7: Final Release Candidate Verification

**Files:**
- Modify: `docs/planning/memory-bank/progress.md`
- Modify: `docs/release/release-candidate-checklist.md`
- Modify: `docs/release/known-issues.md`

- [ ] **Step 1: 顺序执行完整验收剧本**

按 `docs/release/demo-script.md` 和 `docs/release/release-candidate-checklist.md` 走一遍完整流程。

- [ ] **Step 2: 收集最终验证证据**

至少记录：

```text
- 单元/集成测试结果
- e2e 或人工冒烟结果
- build 结果
- 关键截图
```

- [ ] **Step 3: 更新 progress.md 的最终状态**

将封板阶段改成完成，并附验证摘要。

- [ ] **Step 4: 明确是否达到交付标准**

使用固定结论模板：

```md
## Release Candidate 结论
- 交付结论：可交付 / 有条件可交付 / 暂不可交付
- 阻断项：
- 接受风险：
- 建议下一步：
```

- [ ] **Step 5: Commit**

```bash
git add docs/planning/memory-bank/progress.md docs/release/release-candidate-checklist.md docs/release/known-issues.md
git commit -m "docs: finalize release candidate verification status"
```

## Recommended Execution Order

1. Task 1 `Build The Release Acceptance Checklist`
2. Task 2 `Raise Coverage To The Minimum Delivery Target`
3. Task 3 `Run End-To-End Smoke Validation`
4. Task 4 `Unify Public Delivery Documentation`
5. Task 5 `Add Trial-Safety Guardrails`
6. Task 6 `Prepare Portfolio And Demo Materials`
7. Task 7 `Final Release Candidate Verification`

## Notes For Implementers

- 任何“顺手优化”都要先问一个问题：是否直接影响正式交付。
- 如果某条链路存在结构性问题，先降级目标，不要临时扩主功能。
- 测试优先覆盖交付主链路，不要为了刷覆盖率去补低价值代码。
- 文档要服务交付，不要把 memory bank 和对外 README 写成两套完全不同的话术。
- 完成每个 Task 后都要回看 `known-issues`，及时更新带风险交付判断。
