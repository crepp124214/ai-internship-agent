# Docker 多环境使用指南

> 📋 **作品集说明**：本项目是一个 AI 实习求职 Agent 系统，帮助学生进行岗位探索、简历优化和面试准备。

## 演示环境 vs 生产环境

| 功能 | 演示环境 (dev) | 生产环境 (prod) |
|------|---------------|-----------------|
| AI 功能（简历优化、面试教练） | 预设响应（mock） | 真实 LLM 调用 |
| 数据 CRUD（简历、岗位、面试） | ✅ 真实保存 | ✅ 真实保存 |
| Agent 配置页面 | 可查看界面 | 可保存配置 |
| LLM 配置生效 | ❌ 需生产环境 | ✅ 真实 API 调用 |

### 开发环境（推荐演示）

```bash
docker-compose --env-file .env.dev up --build
```

特点：
- 使用 mock LLM，不需要 API 密钥即可体验完整功能流程
- 热重载开启，修改代码自动生效
- 自动创建示例数据（种子数据）

访问：
- 前端：http://localhost:3000
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

### 生产环境

```bash
docker-compose --env-file .env.prod up --build -d
```

特点：
- 使用真实 LLM（需要配置有效的 API Key）
- 优化构建，镜像更小
- 不自动创建示例数据

**重要**：生产环境部署前必须修改 `.env.prod` 中的 LLM 配置：
- `MINIMAX_API_KEY` 或其他 provider 的 API Key
- `SECRET_KEY`

### 测试环境

```bash
docker-compose -f docker-compose.test.yml up --build
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
cp .env.local.example .env
```

2. 修改 .env 中的配置

3. 启动（会自动加载 docker-compose.override.yml）：
```bash
docker-compose up --build
```

## 环境变量文件说明

| 文件 | 用途 | 是否提交 |
|------|------|---------|
| `.env.dev` | 开发/演示环境配置 | 是 |
| `.env.prod` | 生产环境配置 | 是 |
| `.env.local` | 本地默认配置示例 | 是 |
| `.env` | 本地实际配置 | 否（已 gitignore） |
| `docker-compose.override.yml` | 本地开发覆盖 | 否（已 gitignore） |

## 注意事项

- `.env.local.example` 是本地默认配置示例
- `.env.prod` 包含占位符，生产环境部署前必须修改 `SECRET_KEY` 和 LLM API Key
- `docker-compose.override.yml` 用于本地开发，会自动被 gitignore，不提交到仓库
