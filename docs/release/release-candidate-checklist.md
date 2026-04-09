# Release Candidate 交付验收清单

> 版本: v1.1.0 | 日期: 2026-04-09 | 目标: 正式小范围试用 + 招聘作品集展示

## 交付结论

**交付结论：有条件可交付**

| 类别 | 状态 | 说明 |
|------|------|------|
| 主链路可跑通 | ✅ | 岗位保存→简历优化→面试→设置中心可串联 |
| 自动化测试通过 | ⚠️ | 534 passed，1 failed（README 测试格式问题，不影响功能） |
| 覆盖率 | ⚠️ | 79.66%，原始目标 85%，差距 5.34%（见下方说明） |
| demo 环境能启动 | ✅ | `LLM_PROVIDER=mock` 可启动 |
| 文档口径一致 | ✅ | 本次修正后统一 |
| 已知风险已记录 | ✅ | 见"已知问题"节 |

**发布限制**：覆盖率未达原始 85% 目标，属于质量层面的发布约束，后续代码演进风险增加，但不阻断当前 demo 试用。

---

## 覆盖率说明（正文口径）

| 指标 | 值 | 说明 |
|------|-----|------|
| pytest.ini 门槛 | 79% | Phase 13 时从 85% 下调至此（见 `pytest.ini` 第 24 行） |
| 实际测得覆盖率 | 79.66% | 刚好压线 |
| 原始目标（implementation-plan） | 85% | Phase 15 规划目标，**当前未达到** |
| 本次新增测试 | +7 个 | `POST /jobs/save-external` 集成测试 |

> **发布限制说明**：79.66% 已过 pytest.ini 当前门槛（79%），但低于 implementation-plan 原始目标（85%）。差距 5.34 个百分点，属于质量约束，不影响 demo 试用，但需在后续迭代中补齐。

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
| 单元/集成测试（排除 entity tests） | `APP_ENV=development python -m pytest tests/unit tests/integration --ignore=tests/unit/data_access/test_entities.py -q` | ⚠️ 534 passed, 1 failed, 18 skipped |
| 覆盖率 | `APP_ENV=development python -m pytest tests/unit tests/integration --cov=src --cov-report=term --ignore=tests/unit/data_access/test_entities.py` | ⚠️ 79.66%（未达原始目标 85%，已过 pytest.ini 门槛 79%） |
| 前端 Build | `npm run build` | ✅ 通过 |
| entity tests（需 Docker PG） | `python -m pytest tests/unit/data_access/test_entities.py` | ⚠️ 28 errors（需 Docker PostgreSQL，CI 专属） |

---

## 已知问题

| 问题 | 影响范围 | 是否阻断交付 | 临时规避 | 后续修复建议 |
|------|----------|------------|----------|------------|
| 覆盖率未达原始目标 85% | 质量保证 | 否（质量约束，不阻断 demo 试用） | pytest.ini 门槛现为 79%，当前 79.66% 刚好过线 | 补充对 `interview.py`（44%覆盖率）和 `resume.py`（47%覆盖率）的测试，目标恢复至 85% |
| `test_readme_declares_demo_flow` 断言格式不符 | CI 测试 | 否 | README 已包含 demo 账号信息，仅格式不同 | 更新测试断言匹配当前 README 格式 |
| entity tests 需 Docker PostgreSQL | 本地 schema drift 验证 | 否 | CI 环境中运行 | 创建 `.env.test` 专门用于测试环境 |
| coach interview API 集成测试覆盖不足 | 回归保护 | 否 | 手动测试关键流程 | 补充 coach start/answer/report 的集成测试 |
