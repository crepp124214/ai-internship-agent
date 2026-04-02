# 开发者指南

本指南面向开发者，帮助快速上手 ai-internship-agent 项目，并提供长期维护的规范与实践。

## 1. 架构总览（三层架构）

- 表现层 (Presentation) - 路由、请求/响应、依赖注入、异常转换
- 控制逻辑层 (Business Logic) - 业务服务、任务编排、领域逻辑、Agent 协作
- 数据持久层 (Data Access) - 数据库连接、ORM 实体、Repository、迁移逻辑
- 核心基础设施层 (Core) - LLM 抽象、memory、tools、跨层公共能力

目录约定：
- 表现层：src/presentation/
- 控制逻辑层：src/business_logic/
- 数据持久层：src/data_access/
- 核心基础设施：src/core/

ASCII 结构示意：
```
Client -> Presentation/API -> Business Logic -> Data Access
                                ↑               ↓
                               Core (LLM, memory, tools)
```

## 2. 本地开发环境搭建

1) 克隆仓库
- git clone <your-repo-url>
- cd ai-internship-agent

2) 创建并激活虚拟环境
- Windows: python -m venv venv && venv\Scripts\activate
- macOS/Linux: python3 -m venv venv && source venv/bin/activate

3) 安装依赖
- pip install -r requirements.txt

4) 复制并配置环境变量
- 参考 .env.example，创建 .env
- 常用变量示例:
  - DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
  - OPENAI_API_KEY=sk-...
  - APP_ENV=development
  - SECRET_KEY=change-me

5) 数据库迁移与种子数据
- Alembic 迁移：alembic upgrade head
- 如有 seeds 脚本，执行（如：python -m scripts.seed_initial_data）

6) 启动应用
- uvicorn main:app --reload --host 0.0.0.0 --port 8000
- 或使用 Makefile：make dev

7) 常用测试与验证
- 单元测试：make test-unit
- 集成测试：make test-integration
- 端到端测试：make test-e2e

## 3. 如何新增领域域（示例：新增 Project 领域）

1) 在业务层新增领域服务：src/business_logic/project/
2) 在表现层暴露路由：src/presentation/routers/project.py，绑定到 FastAPI app
3) 在数据层增加模型与迁移：src/data_access/models/project.py，生成 alembic migration
4) 编写单元/集成测试，确保契约不破坏
5) 更新必要的文档和示例

## 4. 如何新增一个 LLM 提供商（Provider）

1) 查看核心层的 LLM 工厂实现：src/core/llm/factory.py
2) 实现新的 Provider 类，遵循 LLMProvider 接口（输入/输出统一格式）
3) 将新 provider 注册到工厂，确保按配置选择实现
4) 增加对应单元测试

## 5. 代码风格与约束
- 使用 Black 进行格式化，Isort 进行排序
- 最大行宽 100
- 强制使用类型注解，尽量添加有意义的注释
- 代码结构遵循 "单一职责、清晰边界" 原则

## 6. 数据库迁移
使用 Alembic 进行迁移：
- alembic revision --autogenerate -m "描述信息"
- alembic upgrade head

## 7. 常见问题排查
- 数据库锁定导致无法连接：确保没有其他进程持有锁，必要时取消并重建连接
- 导入错误：确认依赖已安装、PYTHONPATH 正确、环境变量就绪
- 依赖版本冲突：使用 requirements.txt 中锁定的版本

## 8. 参考与引用
- 本文档将引用根仓库的 README，以及 docs/ 目录中的其他文档，避免重复内容。

本文档旨在帮助新成员快速搭建开发环境和理解项目结构，后续如有变更，将以代码为准并在该文档中及时更新。
