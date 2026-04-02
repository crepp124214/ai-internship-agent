# 发布检查清单

在把这个后端称为“可发布”之前，先过一遍这份清单。

## 配置

- [ ] `.env` 已存在，并且基于 [`.env.example`](../.env.example)
- [ ] `SECRET_KEY` 不是占位值
- [ ] `LLM_PROVIDER` 对当前目标环境是有意选择的
- [ ] 当使用真实 provider 时，所需 API Key 已配置
- [ ] `CORS_ORIGINS` 与目标前端环境匹配

## 数据库与运行时

- [ ] 数据库迁移执行成功
- [ ] `GET /health` 返回 `200`
- [ ] `GET /ready` 返回 `200`
- [ ] 应用使用预期的 `DATABASE_URL` 启动
- [ ] 应用使用预期的 `REDIS_URL` 启动

## 验证

- [ ] `python -m pytest tests/integration/api/test_system_api.py tests/e2e/test_user_flow.py --no-cov -q`
- [ ] `python -m pytest tests/integration/api/test_resume_api.py tests/integration/api/test_interview_api.py tests/integration/api/test_jobs_api.py tests/integration/api/test_tracker_api.py tests/e2e/test_user_flow.py --no-cov -q`

## Compose 发布式路径

- [ ] `docker compose -f docker/docker-compose.yml up --build` 能成功启动
- [ ] `postgres` 变为 healthy
- [ ] `redis` 变为 healthy
- [ ] `app` 能通过 `/ready` 进入 healthy

## 产品路径

- [ ] 能通过 `POST /api/v1/users/login/` 登录
- [ ] 能通过 `GET /api/v1/users/me` 获取当前用户
- [ ] 登录后 resume summary 受保护路径可用
- [ ] 至少有一条已持久化的 AI 历史路径可读

## 文档

- [ ] [`README.md`](../README.md) 与当前运行路径一致
- [ ] [`docs/deployment.md`](./deployment.md) 与当前 Compose 路径一致
- [ ] [`PROJECT_MEMORY.md`](../PROJECT_MEMORY.md) 已记录本次交付阶段的最终说明
