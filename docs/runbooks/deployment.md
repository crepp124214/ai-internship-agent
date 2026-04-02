# 部署运行手册

本文档面向运维与开发运维，描述从开发到生产的部署与运维流程。

## 1. 前提条件
- Docker 与 Docker Compose 已安装
- Python 3.11（用于本地相关脚本与迁移）
- 访问权限：数据库、外部服务（如 OpenAI）密钥等配置项可用

## 2. 环境变量参考
- 复制 .env.example 为 .env，按实际环境填写：
  - DATABASE_URL=postgresql://user:pass@host:5432/dbname
  - OPENAI_API_KEY=sk-...
  - SECRET_KEY=change-me
  - APP_ENV=production
- 其他隐藏配置请保持在 .env 文件中，确保容器可读取。

## 3. 使用 Docker Compose 部署
- 启动（后台模式）
  docker compose -f docker/docker-compose.yml up -d
- 如需重新构建镜像：
  docker compose -f docker/docker-compose.yml up -d --build

## 4. 数据库迁移（生产环境）
- 在容器内执行 Alembic 迁移（推荐在部署完成后执行一次）
  docker compose exec app alembic upgrade head
- 或通过 Makefile：make migrate

## 5. 健康检查
- 端点：/health
- curl -sS http://localhost:8000/health

## 6. 查看日志
- 关注应用日志：
  docker compose logs -f app

## 7. 回滚部署
- 停止并下线当前服务：
  docker compose down
- 拉取最新镜像并重新启动：
  docker compose pull
  docker compose up -d

## 8. 备份与恢复数据库
- 备份（PostgreSQL）：
  pg_dump -U <user> -h <host> -d <dbname> -F c -f backup.dump
- 恢复：
  pg_restore -U <user> -h <host> -d <dbname> backup.dump

## 9. 伸缩性考虑
- 若需要水平扩展，参考容器编排工具或运行时环境，示例（基于 compose 的简单伸缩）：
  docker compose up -d --scale app=2 -f docker/docker-compose.yml

> 备注：本文件中的命令以项目实际的 docker-compose.yml 布局为准，必要时请调整服务名称。
