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
| `.env.dev` | 开发环境配置 | 是 |
| `.env.prod` | 生产环境配置 | 是 |
| `.env.local` | 本地默认配置示例 | 是 |
| `.env` | 本地实际配置 | 否（已 gitignore） |
| `docker-compose.override.yml` | 本地开发覆盖 | 否（已 gitignore） |

## 注意事项

- `.env.local.example` 是本地默认配置示例
- `.env.dev` 和 `.env.prod` 包含占位符，需要根据实际情况修改
- 生产环境部署前务必修改 `SECRET_KEY` 和 `MINIMAX_API_KEY`
- `docker-compose.override.yml` 用于本地开发，会自动被 gitignore，不提交到仓库
