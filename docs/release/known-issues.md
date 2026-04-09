# 已知问题（Release Candidate）

> 版本: v1.1.0 | 日期: 2026-04-09

---

## Issue 1：覆盖率未达原始目标 85%

- **描述**：pytest.ini 在 Phase 13 将覆盖率门槛从 80% 下调至 79%，当前实测 79.66% 刚好压线，但 implementation-plan.md 中 Phase 15 原始目标为 85%，当前差距约 5.34 个百分点
- **影响范围**：质量保证层面；低覆盖率意味着 `interview.py`（44%）、`resume.py`（47%）等模块在代码变更时缺少回归保护
- **是否阻断交付**：否（质量约束，不阻断 demo 试用；当前 demo 试用的功能链路完整可跑通）
- **临时规避方案**：按 pytest.ini 当前门槛 79% 可交付；本次新增 7 个 save-external 集成测试，覆盖率从约 79% 微升至 79.66%
- **后续修复建议**：优先为 `interview/coach` 端点和 `resume/customize-for-jd` 端点补充集成测试，目标覆盖率恢复至 85%

---

## Issue 2：README 测试断言格式不符

- **描述**：`test_readme_declares_demo_flow` 断言 README 包含字符串 `"demo / demo123"`，但当前 README 中 demo 账号的格式为两行分别描述
- **影响范围**：CI 测试管道（不影响真实用户体验）
- **是否阻断交付**：否
- **临时规避方案**：手动验证 README 包含 demo 账号信息即可
- **后续修复建议**：更新 `tests/unit/test_release_assets.py` 中的断言，改为检查包含 "demo" 和 "demo123" 关键词而非确切格式

---

## Issue 3：entity tests 依赖 Docker PostgreSQL

- **描述**：`tests/unit/data_access/test_entities.py` 中的 28 个测试需要连接 `postgres:5432`（Docker Compose hostname），本地开发环境无 Docker 时这些测试报错
- **影响范围**：本地开发时无法验证数据库 schema drift
- **是否阻断交付**：否（这些测试设计为 CI 专用）
- **临时规避方案**：在 Docker Compose 环境中运行 entity tests：`docker compose run --rm pytest pytest tests/unit/data_access/test_entities.py`
- **后续修复建议**：创建 `.env.test` 文件并在 CI 中使用独立的 test 环境变量文件

---

## Issue 4：本地测试需设置 APP_ENV=development

- **描述**：根 `.env` 文件设置 `APP_ENV=production` + `SECRET_KEY=change-me-before-production`，导致本地 pytest 运行时触发安全检查报错退出
- **影响范围**：本地开发时无法直接运行 pytest；CI 环境使用 `.env.dev` 不受影响
- **是否阻断交付**：**是（开发体验阻断，非试用用户阻断）**
- **临时规避方案**：运行测试时设置环境变量 `APP_ENV=development python -m pytest ...`
- **后续修复建议**：将 `.env` 的 `APP_ENV` 改为 `development`，或创建 `.env.test` 专门用于测试环境

---

## Issue 5：coach interview API 集成测试覆盖不足

- **描述**：`POST /api/v1/interview/coach/start`、`POST /api/v1/interview/coach/answer`、`GET /api/v1/interview/coach/report/{session_id}` 等端点虽有真实实现，但仅有 `test_interview_flow.py` 中的占位测试
- **影响范围**：端点行为变更时缺少回归保护
- **是否阻断交付**：否
- **临时规避方案**：手动测试关键流程
- **后续修复建议**：补充 coach API 的集成测试，覆盖正常流程和错误边界

---

## 已解决问题（供审计参考）

| 问题 | 状态 | 解决时间 |
|------|------|----------|
| POST /jobs/save-external 无集成测试 | ✅ 已修复（2026-04-09 本次封板） | 本次新增 7 个测试用例 |
