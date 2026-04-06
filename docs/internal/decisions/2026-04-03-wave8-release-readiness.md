# Wave 8：发布就绪与稳定性

> **日期**：2026-04-03
> **关联 Wave**：Wave 8 — Stability & Release Readiness
> **决策人**：Main Agent

---

## 背景

Wave 8 目标是提升发布就绪与稳定性，统一验证入口，降低环境差异导致的发布风险。

---

## 决策内容

### D8.1: Dockerfile 启动命令修复
- **问题**：原 Dockerfile 使用 `CMD ["python", "src/main.py"]` 启动，生产环境应使用 uvicorn 多 worker
- **决策**：改为 `CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]`
- **理由**：uvicorn 是 FastAPI 推荐的生产服务器，多 worker 提高并发能力
- **实现**：`docker/Dockerfile` 修改

### D8.2: 容器启动自动迁移
- **问题**：容器启动时不会自动运行数据库迁移
- **决策**：创建 `docker/entrypoint.sh`，先运行迁移再启动应用
- **理由**：确保每次部署时数据库 schema 与代码同步
- **实现**：`docker/entrypoint.sh` 创建，Dockerfile 添加 ENTRYPOINT

### D8.3: Docker 构建优化
- **问题**：Docker 镜像包含不必要的文件（node_modules、tests、logs 等）
- **决策**：创建 `.dockerignore` 排除不必要的文件
- **理由**：减小镜像体积，加快构建和部署
- **实现**：`.dockerignore` 创建

### D8.4: Compose 健康检查自动化
- **问题**：`docker compose up` 后需要手动检查服务是否就绪
- **决策**：创建 `scripts/compose-health.sh` 等待所有服务变为 healthy
- **理由**：自动化部署流程，减少人工干预
- **实现**：`scripts/compose-health.sh` 创建，Makefile 新增 `compose-health` 目标

### D8.5: Makefile compose-up 改为后台启动
- **问题**：`compose-up` 阻塞终端，无法继续执行其他命令
- **决策**：改为 `up --build -d` 后台启动，新增 `compose-health` 等待就绪
- **理由**：符合 CI/CD 最佳实践
- **实现**：`Makefile` 修改

---

## 影响范围

| 影响项 | 文件 | 变更类型 |
|---|---|---|
| Dockerfile | `docker/Dockerfile` | 修改 |
| Entrypoint | `docker/entrypoint.sh` | 新增 |
| Dockerignore | `.dockerignore` | 新增 |
| Health Script | `scripts/compose-health.sh` | 新增 |
| Makefile | `Makefile` | 修改 |

---

## 跟踪执行情况

| 决策项 | 执行状态 | 验证方式 |
|---|---|---|
| Dockerfile 启动命令修复 | ✅ 已完成 | Dockerfile 已更新 |
| 容器启动自动迁移 | ✅ 已完成 | entrypoint.sh 已创建 |
| Docker 构建优化 | ✅ 已完成 | .dockerignore 已创建 |
| Compose 健康检查自动化 | ✅ 已完成 | compose-health.sh 已创建 |
| Makefile compose-up 修改 | ✅ 已完成 | Makefile 已更新 |

---

## 后续行动

- [ ] 在 Docker 环境中验证 `make compose-up && make compose-health` 完整流程
- [ ] 验证数据库迁移在容器启动时自动执行
- [ ] 确认健康检查在 PostgreSQL 和 Redis 就绪后 app 变为 healthy
