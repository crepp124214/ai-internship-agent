# Phase 9：Docker Compose 多环境配置 设计文档

> 版本: v1.0.0 | 状态: 设计完成 | 日期: 2026-04-07

---

## 一、目标

**核心目标：** 使用统一的 `docker-compose.yml`，通过加载不同的 `.env` 文件切换开发/生产环境。

**用户体验：** 开发者可以通过简单的 `docker-compose --env-file .env.dev up` 启动开发环境，或 `docker-compose --env-file .env.prod up` 启动生产环境。

---

## 二、功能详细设计

### 2.1 文件结构

```
.env                    # 默认/本地开发
.env.dev               # 开发环境（mock LLM、热重载）
.env.prod              # 生产环境（真实 LLM、优化构建）
.env.test              # 测试环境（已有）
docker-compose.yml     # 统一配置（已有）
docker-compose.override.yml  # 本地开发覆盖（新增）
```

### 2.2 环境差异

| 配置 | .env.dev | .env.prod |
|------|----------|-----------|
| APP_ENV | development | production |
| APP_DEBUG | true | false |
| LLM_PROVIDER | mock | minimax |
| ENABLE_REAL_LLM | false | true |
| 热重载 | 开启（卷挂载 src） | 关闭 |
| 日志级别 | DEBUG | INFO |

### 2.3 热重载实现

**开发环境：**

```yaml
app:
  volumes:
    - ./src:/app/src:ro
  environment:
    APP_ENV: development
    APP_DEBUG: "true"
    LLM_PROVIDER: mock
```

**生产环境：**

```yaml
app:
  volumes:  # 不挂载源码，使用构建后的二进制
    - ./data:/app/data
  environment:
    APP_ENV: production
    APP_DEBUG: "false"
    LLM_PROVIDER: minimax
```

---

## 三、.env 文件内容

### 3.1 .env.dev（开发环境）

```bash
# 应用配置
APP_NAME=AI Internship Agent
APP_ENV=development
APP_DEBUG=true
APP_HOST=0.0.0.0
APP_PORT=8000

# 数据库
DATABASE_URL=postgresql://agent_user:agent_password@postgres:5432/internship_agent
REDIS_URL=redis://redis:6379/0

# LLM - 开发环境用 mock
LLM_PROVIDER=mock
ENABLE_REAL_LLM=false

# 日志
LOG_LEVEL=DEBUG

# 安全
SECRET_KEY=dev-secret-key-change-in-production

# CORS
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]

# 速率限制
RATE_LIMIT_BACKEND=redis
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60

# 示例数据
SEED_DEMO_ON_BOOT=true
```

### 3.2 .env.prod（生产环境）

```bash
# 应用配置
APP_NAME=AI Internship Agent
APP_ENV=production
APP_DEBUG=false
APP_HOST=0.0.0.0
APP_PORT=8000

# 数据库
DATABASE_URL=postgresql://agent_user:agent_password@postgres:5432/internship_agent
REDIS_URL=redis://redis:6379/0

# LLM - 生产环境用真实 API
LLM_PROVIDER=minimax
MINIMAX_API_KEY=your-api-key-here
MINIMAX_BASE_URL=https://api.minimax.chat/v1
MINIMAX_MODEL=abab6.5g-chat
ENABLE_REAL_LLM=true

# 日志
LOG_LEVEL=INFO

# 安全 - 必须修改
SECRET_KEY=change-this-to-a-secure-random-key

# CORS
CORS_ORIGINS=["https://your-domain.com"]

# 速率限制
RATE_LIMIT_BACKEND=redis
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60

# 示例数据
SEED_DEMO_ON_BOOT=false
```

---

## 四、使用方式

### 4.1 开发环境

```bash
docker-compose --env-file .env.dev up --build
```

### 4.2 生产环境

```bash
docker-compose --env-file .env.prod up --build -d
```

### 4.3 测试环境

```bash
docker-compose -f docker-compose.test.yml --env-file .env.test up --build
```

---

## 五、验收标准

1. `docker-compose --env-file .env.dev up` 启动开发环境，使用 mock LLM
2. `docker-compose --env-file .env.prod up` 启动生产环境，使用真实 LLM
3. 开发环境修改源码后，容器内自动重载（热重载生效）
4. 生产环境镜像构建优化，体积更小
5. 各环境配置文件分离，不泄露敏感信息

---

## 六、文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| .env.dev | 新增 | 开发环境配置 |
| .env.prod | 新增 | 生产环境配置 |
| docker-compose.override.yml | 新增 | 本地开发覆盖配置 |
| .env.compose | 修改 | 改为 .env.local 示例 |
