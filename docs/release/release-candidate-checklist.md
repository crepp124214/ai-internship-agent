# Release Candidate 交付验收清单

> 版本: v1.2.0 | 日期: 2026-04-09 | 目标: 正式小范围试用 + 招聘作品集展示

## 交付结论

**交付结论：有条件可交付**

| 类别 | 状态 | 说明 |
|------|------|------|
| 主链路可跑通 | ✅ | 岗位保存→简历优化→面试→设置中心可串联 |
| 自动化测试通过 | ✅ | 563 passed, 18 skipped（unit/integration，排除 entity tests） |
| 覆盖率 | ✅ | 80.17%，达到 pytest.ini 门槛 80% |
| Phase C 连续跑 | ✅ | 前后端各 20/20（100%），达到 >=95% 标准 |
| demo 环境能启动 | ✅ | `LLM_PROVIDER=mock` 可启动 |
| 文档口径一致 | ✅ | 与 known-issues.md 统一 |
| 已知风险已记录 | ✅ | 见"已知问题"节 |

**发布限制**：覆盖率 80.17% 达到 pytest.ini 门槛（80%），但低于 implementation-plan 原始目标（85%）。低覆盖率模块（resume.py 47%、auth.py 30%）为后续质量风险。

---

## 覆盖率说明（正文口径）

| 指标 | 值 | 说明 |
|------|-----|------|
| pytest.ini 门槛 | 80% | 本次封板从 79% 提升至 80% |
| 实际测得覆盖率 | 80.17% | 刚好压线 |
| 原始目标（implementation-plan） | 85% | Phase 15 规划目标，**当前未达到** |
| 本次新增测试 | +16 个 | coach API 集成测试 + interview.py 覆盖率提升至 61% |

> **发布限制说明**：80.17% 已过 pytest.ini 当前门槛（80%），但低于 implementation-plan 原始目标（85%）。差距约 5 个百分点，属于质量约束，不影响 demo 试用，但需在后续迭代中补齐低覆盖率模块（resume.py 47%、auth.py 30%）。

---

## 必过链路

### 链路 1：登录 demo 账号并进入系统首页

- **前置条件**：Docker Compose 环境已启动，或本地 PostgreSQL + Redis + Backend + Frontend 已运行，`SEED_DEMO_ON_BOOT=true`
- **操作步骤**：
  1. 访问 http://localhost:3000
  2. 使用 demo 账号登录（用户名：`demo`，密码：`demo123`）
  3. 观察首页加载
- **预期结果**：登录成功，跳转首页，显示仪表盘
- **实际结果**：
- **负责人**：
- **验收日期**：

---

### 链路 2：岗位探索页完成岗位导入或创建，并保存岗位

- **前置条件**：已登录，进入岗位探索页面（`/jobs-explore`）
- **操作步骤**：
  1. 在岗位探索页面，通过 Agent 对话搜索公司招聘官网，或手动创建岗位
  2. 填写必填字段：岗位标题、公司、地点、岗位描述
  3. 点击"收藏到岗位库"（调用 `POST /api/v1/jobs/save-external`）
  4. 观察岗位出现在岗位列表
- **预期结果**：岗位保存成功，列表中出现收藏的岗位
- **实际结果**：
- **负责人**：
- **验收日期**：

---

### 链路 3：从岗位上下文进入简历优化并完成一次 JD 定向优化

- **前置条件**：已有简历和目标 JD
- **操作步骤**：
  1. 进入简历优化页面 `/resume`
  2. 选择已导入的简历
  3. 上传 JD 或从已保存岗位获取 JD 上下文
  4. 点击"定向优化"（调用 `POST /api/v1/resume/customize-for-jd`）
  5. 等待 Agent 优化完成
- **预期结果**：展示优化后的简历，包含匹配度报告
- **实际结果**：
- **负责人**：
- **验收日期**：

---

### 链路 4：从简历优化进入面试准备并开始一次面试会话

- **前置条件**：已完成简历优化，有 JD 上下文
- **操作步骤**：
  1. 进入面试准备页面 `/interview`
  2. 选择简历（关联 JD）
  3. 点击"开始面试对练"（调用 `POST /api/v1/interview/coach/start`）
  4. 回答 AI 提出的问题（调用 `POST /api/v1/interview/coach/answer`）
  5. 结束面试（调用 `POST /api/v1/interview/coach/end`），获取复盘报告
- **预期结果**：面试会话正常进行，结束后有评分和复盘报告
- **实际结果**：
- **负责人**：
- **验收日期**：

---

### 链路 5：在设置中心查看面试记录并校验 Agent 配置页面可用

- **前置条件**：已完成至少一次面试会话
- **操作步骤**：
  1. 进入设置中心 `/settings`
  2. 选择"面试记录"标签页
  3. 查看历史面试会话列表，点击查看详情（调用 `GET /api/v1/interview/coach/report/{session_id}`）
  4. 选择"Agent 配置"标签页
  5. 切换 LLM Provider，验证配置保存（调用 `POST /api/v1/user-llm-configs`）

- **预期结果（按环境区分）**：

  | 环境 | 预期行为 |
  |------|----------|
  | **demo 模式**（`LLM_PROVIDER=mock`） | Agent 配置页面可展示，但 Provider 下拉切换后保存无真实 AI 效果，响应内容为 mock 输出 |
  | **非 demo 模式**（`LLM_PROVIDER=openai/minimax`） | Agent 配置可正常切换保存，接入真实 AI |

  > **口径说明**：README 明确指出 demo 模式下 Agent 功能受限。本验收项在 demo 模式下验收"配置可操作"，而非"配置有真实 AI 效果"。后者需要切换到真实 provider。

- **实际结果**：
- **负责人**：
- **验收日期**：

---

## 自动化验证结果

| 验证项 | 命令 | 结果 |
|--------|------|------|
| 单元/集成测试（排除 entity tests） | `APP_ENV=development python -m pytest tests/unit tests/integration --ignore=tests/unit/data_access/test_entities.py -q` | ✅ 563 passed, 18 skipped |
| 覆盖率 | `APP_ENV=development python -m pytest tests/unit tests/integration --cov=src --cov-fail-under=80 --ignore=tests/unit/data_access/test_entities.py` | ✅ 80.17%（达到门槛 80%） |
| 前端测试 | `npm test` | ✅ 34 passed |
| 前端 Build | `npm run build` | ✅ 通过 |
| entity tests（需 Docker PG） | `python -m pytest tests/unit/data_access/test_entities.py` | ⚠️ 28 errors（需 Docker PostgreSQL，CI 专属） |

---

## Phase C 连续跑结果

| 维度 | 任务号 | 结果 |
|------|--------|------|
| 后端/API 连续跑 | `20260409-200629-452-46176` | ✅ PASS，20/20，100% |
| 前端主链路连续跑 | `20260409-200629-538-47700` | ✅ PASS，20/20，100% |

Phase C 封板判定：

- 连续 20 次主链路通过率 >=95%：✅ 达成（100%）
- P0/P1 问题：✅ 0
- request_id 可追踪：✅ 达成

---

## 已知问题

| 问题 | 影响范围 | 是否阻断交付 | 临时规避 | 后续修复建议 |
|------|----------|------------|----------|------------|
| 覆盖率未达原始目标 85% | 质量保证 | 否（质量约束，不阻断 demo 试用） | pytest.ini 门槛已设为 80%，当前 80.17% 刚好压线 | 补充 `interview.py`（61%）和 `resume.py`（47%）的测试，目标恢复至 85% |
| entity tests 需 Docker PostgreSQL | 本地 schema drift 验证 | 否 | CI 环境中运行 | Docker Compose 环境中运行 |
| coach interview API 集成测试覆盖不足 | 回归保护 | 否 | 手动测试关键流程 | ✅ 已修复（2026-04-09），新增 9 个 coach API 测试 |
| 低覆盖率模块（resume.py 47%、auth.py 30%） | 代码变更回归保护 | 否（质量约束） | 手动验证 | 优先为简历定制、用户认证相关端点补充集成测试 |
