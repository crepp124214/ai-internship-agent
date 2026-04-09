# 已知问题（Release Candidate）

> 版本: v1.1.1 | 日期: 2026-04-09

---

## Issue 1：entity tests 依赖 Docker PostgreSQL

- **描述**：`tests/unit/data_access/test_entities.py` 中的 28 个测试需要连接 `postgres:5432`（Docker Compose hostname），本地开发环境无 Docker 时这些测试报错
- **影响范围**：本地开发时无法验证数据库 schema drift
- **是否阻断交付**：否（这些测试设计为 CI 专用）
- **临时规避方案**：在 Docker Compose 环境中运行 entity tests：`docker compose run --rm pytest pytest tests/unit/data_access/test_entities.py`

---

## Issue 2：覆盖率门槛 80%

- **描述**：pytest.ini 设置 `--cov-fail-under=80`，当前覆盖率 80.17%，刚好压线
- **影响范围**：质量保证层面
- **是否阻断交付**：否
- **后续修复建议**：继续为低覆盖率模块（`interview.py` 61%、`resume.py` 47%）补充集成测试

---

## Issue 3：本地测试需设置 APP_ENV=development

- **描述**：根 `.env` 文件设置 `APP_ENV=production` + `SECRET_KEY=change-me-before-production`，导致本地 pytest 运行时触发安全检查报错退出
- **影响范围**：本地开发时无法直接运行 pytest
- **是否阻断交付**：**是（开发体验阻断，非试用用户阻断）**
- **临时规避方案**：
  - 运行测试时设置环境变量：`APP_ENV=development python -m pytest ...`
  - 或使用 `.env.test` 配置文件：`cp .env.test .env && python -m pytest ...`
- **后续修复建议**：CI 已使用 `.env.dev`，本地开发推荐使用 `.env.test`

---

## Issue 4：低覆盖率模块

- **描述**：`resume.py`（47%）、`auth.py`（30%）、`users.py`（37%）等模块覆盖率偏低
- **影响范围**：代码变更时缺少回归保护
- **是否阻断交付**：否
- **后续修复建议**：优先为简历定制、用户认证相关端点补充集成测试

---

## 已解决问题（供审计参考）

| 问题 | 状态 | 解决时间 |
|------|------|----------|
| 覆盖率门槛从 79% 提升至 80% | ✅ 已修复（2026-04-09） | pytest.ini 更新为 80% |
| coach interview API 集成测试覆盖不足 | ✅ 已修复（2026-04-09） | 新增 9 个 coach API 测试 |
| 本地测试 APP_ENV/SECRET_KEY 问题 | ✅ 已修复（2026-04-09） | 新增 `.env.test` 配置文件 |
| POST /jobs/save-external 无集成测试 | ✅ 已修复（2026-04-09） | 新增 7 个测试用例 |
| `test_readme_declares_demo_flow` 断言格式不符 | ✅ 已修复（2026-04-09） | 断言已更新 |
