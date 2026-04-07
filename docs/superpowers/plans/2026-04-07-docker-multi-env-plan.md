# Docker Compose 多环境配置 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 使用统一的 docker-compose.yml，通过 .env 文件切换开发/生产环境

**Architecture:** 统一的 docker-compose.yml 定义所有服务，不同 .env 文件提供不同配置，通过 --env-file 切换

**Tech Stack:** Docker Compose, Python, Environment Variables

---

## 文件结构

```
.env.dev               # 新增：开发环境配置
.env.prod              # 新增：生产环境配置
docker-compose.override.yml  # 新增：本地开发覆盖
.env.compose           # 重命名为 .env.local 作为本地默认
```

---

## Task 1: 创建 .env.dev 开发环境配置

**Files:**
- Create: `.env.dev`

- [ ] **Step 1: 创建 .env.dev**

```bash
# Docker Compose 开发环境配置
# 使用方式: docker-compose --env-file .env.dev up

# 应用配置
APP_NAME=AI Internship Agent
APP_ENV=development
APP_DEBUG=true
APP_HOST=0.0.0.0
APP_PORT=8000

# 数据库
DATABASE_URL=postgresql://agent_user:agent_password@postgres:5432/internship_agent
REDIS_URL=redis://redis:6379/0

# LLM - 开发环境用 mock，不花钱
LLM_PROVIDER=mock
ENABLE_REAL_LLM=false

# Chroma DB
CHROMA_DB_PATH=./data/vectors/chroma

# 日志
LOG_LEVEL=DEBUG
LOG_FILE=

# 安全
SECRET_KEY=dev-secret-key-change-in-production

# CORS
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]

# 速率限制
RATE_LIMIT_BACKEND=redis
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60

# 示例数据 - 开发环境自动创建
SEED_DEMO_ON_BOOT=true
```

- [ ] **Step 2: 提交**

```bash
git add .env.dev
git commit -m "feat(docker): add .env.dev for development environment"
```

---

## Task 2: 创建 .env.prod 生产环境配置

**Files:**
- Create: `.env.prod`

- [ ] **Step 1: 创建 .env.prod**

```bash
# Docker Compose 生产环境配置
# 使用方式: docker-compose --env-file .env.prod up -d

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

# Chroma DB
CHROMA_DB_PATH=./data/vectors/chroma

# 日志
LOG_LEVEL=INFO
LOG_FILE=

# 安全 - 必须修改
SECRET_KEY=change-this-to-a-secure-random-key-in-production

# CORS - 生产环境需要配置自己的域名
CORS_ORIGINS=["https://your-domain.com"]

# 速率限制
RATE_LIMIT_BACKEND=redis
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60

# 示例数据 - 生产环境不自动创建
SEED_DEMO_ON_BOOT=false
```

- [ ] **Step 2: 提交**

```bash
git add .env.prod
git commit -m "feat(docker): add .env.prod for production environment"
```

---

## Task 3: 创建 docker-compose.override.yml 本地开发覆盖

**Files:**
- Create: `docker-compose.override.yml`

- [ ] **Step 1: 创建 docker-compose.override.yml**

```yaml
# docker-compose.override.yml - 本地开发覆盖配置
# 当运行 docker-compose up 时会自动加载此文件
# 与 docker-compose.yml 合并，提供开发友好的默认配置

services:
  app:
    volumes:
      - ./src:/app/src:ro
    environment:
      APP_ENV: development
      APP_DEBUG: "true"
    healthcheck:
      disabled: true

  frontend:
    volumes:
      - ./frontend/src:/app/src:ro
    healthcheck:
      disabled: true
```

- [ ] **Step 2: 提交**

```bash
git add docker-compose.override.yml
git commit -m "feat(docker): add docker-compose.override.yml for local development"
```

---

## Task 4: 更新 .env.compose 为本地默认示例

**Files:**
- Rename: `.env.compose` → `.env.local`

- [ ] **Step 1: 重命名 .env.compose 为 .env.local**

```bash
mv .env.compose .env.local
```

- [ ] **Step 2: 更新 .gitignore 确保 .env.local 不被提交**

检查 .gitignore 是否包含 .env.local，如果是则移除，因为这是本地示例文件

- [ ] **Step 3: 提交**

```bash
git add .gitignore 2>/dev/null || true
git mv .env.compose .env.local
git commit -m "refactor(docker): rename .env.compose to .env.local as local default"
```

---

## Task 5: 创建使用说明

**Files:**
- Create: `docker/README.md`

- [ ] **Step 1: 创建 docker/README.md**

```markdown
# Docker 多环境使用指南

## 快速开始

### 开发环境（推荐）

```bash
docker-compose --env-file .env.dev up --build
```

特点：
- 使用 mock LLM，不花 API 费用
- 热重载开启，修改代码自动生效
- 自动创建示例数据

访问：
- 前端：http://localhost:3000
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

### 生产环境

```bash
docker-compose --env-file .env.prod up --build -d
```

特点：
- 使用真实 LLM（需要配置 MINIMAX_API_KEY）
- 优化构建，镜像更小
- 不自动创建示例数据

### 测试环境

```bash
docker-compose -f docker-compose.test.yml --env-file .env.test up --build
```

## 环境切换

```bash
# 停止当前环境
docker-compose down

# 切换到开发环境
docker-compose --env-file .env.dev up --build

# 切换到生产环境
docker-compose --env-file .env.prod up --build -d
```

## 本地开发

如果你想本地开发并使用 Docker：

1. 复制环境配置：
```bash
cp .env.local .env
```

2. 修改 .env 中的配置

3. 启动（会自动加载 docker-compose.override.yml）：
```bash
docker-compose up --build
```

## 注意事项

- .env.local 是本地默认配置示例，不提交到 git
- .env.dev 和 .env.prod 包含占位符，需要根据实际情况修改
- 生产环境部署前务必修改 SECRET_KEY 和 MINIMAX_API_KEY
```

- [ ] **Step 2: 提交**

```bash
git add docker/README.md
git commit -m "docs(docker): add multi-env usage guide"
```

---

## Task 6: 验证配置

- [ ] **Step 1: 验证 docker-compose 配置**

```bash
docker-compose --env-file .env.dev config
```

Expected: 无错误，输出合并后的配置

- [ ] **Step 2: 验证 .env.prod 配置**

```bash
docker-compose --env-file .env.prod config
```

Expected: 无错误，输出生产配置

- [ ] **Step 3: 提交**

```bash
git add -A
git commit -m "feat(docker): complete multi-environment Docker configuration"
```

---

## 验收标准检查

- [ ] .env.dev 包含开发环境所需配置
- [ ] .env.prod 包含生产环境所需配置
- [ ] docker-compose.override.yml 提供热重载配置
- [ ] .env.compose 已重命名为 .env.local
- [ ] docker/README.md 包含使用说明
- [ ] docker-compose --env-file .env.dev config 验证通过
- [ ] docker-compose --env-file .env.prod config 验证通过
