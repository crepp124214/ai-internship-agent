# AI 实习求职 Agent 系统

这是一个围绕实习求职流程提供智能辅助能力的全栈演示项目。

当前仓库包含：

- FastAPI 后端
- React + Vite 前端工作台
- Resume / Job / Interview / Tracker 四条核心业务链路
- 本地迁移、种子数据和基础演示脚本

## 项目定位

当前项目定位为“可演示、可联调、可验证”的产品化工程，而不是一次性脚本集合。

重点关注：

- 清晰的三层架构
- 稳定的 API 契约
- 可回归的测试基线
- 前后端能够走通的一条完整演示链路

## 当前阶段

已完成阶段：

- Wave 1: Foundation
- Wave 2: Core MVP
- Wave 3: Observability & Resilience
- Wave 4: Public API & Demo Baseline
- Wave 5: Frontend Productization

下一推荐阶段：

- Wave 6: Frontend Capability Completion

## 快速开始

### 1. 安装依赖

后端：

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

前端：

```bash
cd frontend
npm install
cd ..
```

### 2. 准备环境变量

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env
```

常见本地配置：

- `DATABASE_URL=sqlite:///./data/app.db`
- `LLM_PROVIDER=mock`
- `VITE_API_BASE_URL=http://127.0.0.1:8000`

### 3. 执行迁移

```bash
python scripts/migrate.py
```

### 4. 准备演示数据

```bash
python scripts/seed_demo.py
```

默认演示账号：

- 用户名：`demo`
- 密码：`demo123`

### 5. 启动后端

```bash
make dev
```

### 6. 启动前端

```bash
cd frontend
npm run dev
```

## 官方演示链路

建议按这个顺序体验：

1. 登录
2. 仪表盘
3. 简历中心
4. 岗位匹配工作区
5. 面试准备工作区
6. 投递追踪工作区

## 常用命令

```bash
make test
make test-unit
make test-integration
make test-e2e
```

前端：

```bash
cd frontend
npm run build
npm test
```

## 相关文档

- 项目规则：`AGENTS.md`
- 项目记忆：`PROJECT_MEMORY.md`
- 阶段计划：`.sisyphus/plans/PLAN.md`
- 进度快照：`.sisyphus/plans/progress.md`
- 决策日志：`docs/decisions/README.md`
