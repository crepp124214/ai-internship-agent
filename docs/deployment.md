# 部署说明

这个项目当前只有一条正式支持的“发布式”部署路径：

- 通过 [`docker/docker-compose.yml`](../docker/docker-compose.yml) 使用 Docker Compose

仓库中的 Kubernetes 资产目前还没有被持续维护，因此当前项目的“可发布”定义是围绕 Compose，而不是 `k8s/`。

## 1. 前置条件

- Docker
- Docker Compose v2
- 仓库根目录下准备好的 `.env` 文件

建议从本地安全模板开始：

```bash
cp .env.example .env
```

如果要跑更接近发布的路径，至少要检查这些配置：

- `SECRET_KEY`
- `LLM_PROVIDER`
- `OPENAI_API_KEY` 或 `ANTHROPIC_API_KEY`
- `CORS_ORIGINS`

`docker-compose.yml` 会覆盖数据库和 Redis 地址，让应用指向 Compose 内部服务。

### 2.1 生产环境 CORS 配置

部署到生产环境前，**必须**将 `CORS_ORIGINS` 改为实际的前端域名：

```bash
# .env 生产配置示例
CORS_ORIGINS=["https://your-frontend-domain.com"]
```

当前默认配置仅允许本地开发域名（`localhost:3000`、`localhost:4173` 等），不允许任何生产域名。

其他安全相关配置：
- `SECRET_KEY`：生产环境必须使用随机字符串，不使用默认值
- `APP_DEBUG=false`：生产环境必须关闭调试模式
- `RATE_LIMIT_REQUESTS` / `RATE_LIMIT_WINDOW_SECONDS`：根据实际流量调整限流参数

## 2. 启动整套服务

```bash
docker compose -f docker/docker-compose.yml up --build
```

或者：

```bash
make compose-up
```

涉及服务：

- `postgres`
- `redis`
- `app`

## 3. 检查就绪状态

服务启动后，检查：

- 存活：`GET /health`
- 就绪：`GET /ready`

例如：

```bash
curl http://localhost:8000/ready
```

只有当 `/ready` 返回 `200` 时，这套发布式栈才算真正就绪。

## 4. 运行迁移

对于本地或 CI 风格运行：

```bash
python scripts/migrate.py
```

对于 Compose 运行，建议在发布前或通过同一个 app 镜像对应的运维步骤执行迁移。当前仓库还没有单独定义 migration container job。

## 5. 停止整套服务

```bash
docker compose -f docker/docker-compose.yml down
```

或者：

```bash
make compose-down
```

## 6. 当前发布边界

当前仓库中的“发布就绪”表示：

- 应用可以从文档化的 env 文件启动
- Compose 能启动 `postgres`、`redis` 和 `app`
- `/health` 和 `/ready` 都可用
- 受保护 smoke 路径和核心 AI 路径回归通过

它**并不**表示：

- Kubernetes 部署已经生产就绪
- refresh-token / session 管理已经完整
- 外部 secrets 管理已经完全接入
- 后台 worker 和异步编排已经完成发布级加固
