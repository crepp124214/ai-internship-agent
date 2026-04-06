# AI 实习求职 Agent 系统

一个面向实习求职流程的全栈项目，后端使用 Python + FastAPI，前端使用 React。

## TL;DR

- 想本地开发：看 [本地开发模式](#本地开发模式)
- 想快速拉起完整环境：看 [docker-compose-演示模式](#docker-compose-演示模式)
- 后端默认地址：`http://127.0.0.1:8000`
- 前端开发地址：`http://127.0.0.1:5173`
- 前端 Compose 地址：`http://127.0.0.1:3000`
- 演示账号：`demo / demo123`

当前项目覆盖 4 条核心业务线：

- `/resume`：简历管理、AI 摘要、优化建议、历史记录
- `/jobs`：岗位管理、岗位匹配、历史记录
- `/interview`：面试题生成、回答评估、记录
- `/tracker`：投递追踪、下一步建议、历史记录

核心目标很明确：可运行、可演示、可验证、可维护。

## 目录

- [先看这里](#先看这里)
- [本地开发模式](#本地开发模式)
- [Docker Compose 演示模式](#docker-compose-演示模式)
- [最小验收](#最小验收)
- [界面概览](#界面概览)
- [演示走查](#演示走查)
- [API 文档](#api-文档)
- [测试](#测试)
- [项目结构](#项目结构)
- [部署提醒](#部署提醒)
- [相关文件](#相关文件)

## 先看这里

如果你只是想尽快把项目跑起来，有两条路径：

1. 本地开发模式
适合日常开发、跑测试、单独调试前后端。

2. Docker Compose 演示模式
适合快速拉起一套完整演示环境。

默认地址：

- 后端：`http://127.0.0.1:8000`
- 前端开发：`http://127.0.0.1:5173`
- 前端 Compose：`http://127.0.0.1:3000`

演示账号：

- `demo / demo123`

需要注意：

- 本地开发模式下，需要手动执行 `python scripts/seed_demo.py`
- Compose 模式下，只有在 `.env.compose` 中把 `SEED_DEMO_ON_BOOT=true` 打开，才会自动创建 demo 账号

## 本地开发模式

适合本地开发、断点调试，以及前后端分开修改。

### 1. 准备环境

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

### 2. 初始化数据库和演示数据

```bash
python scripts/migrate.py
python scripts/seed_demo.py
```

### 3. 启动后端

```bash
make dev
```

Windows 没有 `make` 时，可使用项目里的批处理脚本，或直接运行对应命令。

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

## Docker Compose 演示模式

适合快速演示，或者验证完整容器链路。

### 1. 准备 Compose 配置

```bash
cp .env.compose.example .env.compose
```

如果你希望容器启动时自动创建 demo 账号，把 `.env.compose` 里的这一项改为：

```env
SEED_DEMO_ON_BOOT=true
```

### 2. 启动

```bash
make compose-up
```

等价命令：

```bash
docker compose -f docker/docker-compose.yml up --build
```

Compose 会启动以下服务：

- PostgreSQL
- Redis
- 后端 API
- React 前端静态站

前端容器通过同源 `/api` 反向代理访问后端，因此默认不需要额外设置 `VITE_API_BASE_URL`。

## 最小验收

启动成功后，至少确认下面几件事：

1. `GET /health` 返回 `200`
2. `GET /ready` 返回 `200`
3. 可以使用 `demo / demo123` 登录
4. 登录后可以访问受保护页面

## 界面概览

这个项目更像一个围绕求职流程组织的工作台，而不是单点工具集合。

- Resume：维护简历内容，并生成 AI 摘要与优化建议
- Jobs：管理岗位信息，查看匹配结果与历史记录
- Interview：生成面试题，评估回答质量，沉淀记录
- Tracker：记录投递进度，并生成下一步行动建议

如果后续要补对外展示素材，建议优先放这 4 张截图：

1. Dashboard 或首页总览
2. Resume 页的摘要/优化建议结果
3. Jobs 页的岗位匹配结果
4. Tracker 页的下一步建议

## 截图说明文案

如果你准备把项目放到 GitHub 首页、作品集或投递材料里，下面这组截图文案可以直接配合界面使用。

### 1. Dashboard / 首页总览

建议配文：

> 一个围绕实习求职流程组织的工作台首页，把简历、岗位、面试和投递追踪四条主线集中到同一个入口里，方便快速进入当前任务。

适合强调：

- 这是一个完整工作流，不是单个页面 demo
- 信息入口清晰，适合作为项目第一印象

### 2. Resume 页面

建议配文：

> Resume 页面支持简历内容管理，并提供 AI 摘要与优化建议，帮助用户把原始简历整理成更适合目标岗位的版本。

适合强调：

- 既有内容管理，也有 AI 辅助能力
- 不只是生成结果，还能保留历史记录

### 3. Jobs 页面

建议配文：

> Jobs 页面用于维护岗位信息，并结合简历生成岗位匹配结果，帮助用户快速判断当前岗位的契合度与改进方向。

适合强调：

- 把岗位信息和简历分析串起来
- 更贴近真实求职决策，而不是静态列表展示

### 4. Interview 页面

建议配文：

> Interview 页面支持面试题生成、回答评估与记录沉淀，让面试准备过程可以重复、对比和追踪。

适合强调：

- 面试准备不是一次性输出，而是持续练习流程
- 页面同时覆盖生成、评估、记录三个动作

### 5. Tracker 页面

建议配文：

> Tracker 页面负责管理投递状态，并生成下一步行动建议，帮助用户把“已投递”变成“可持续推进”的求职流程。

适合强调：

- 不只记录状态，还提供下一步建议
- 最能体现这个项目的流程闭环能力

### 推荐展示顺序

如果你只放 3 张图，建议顺序是：

1. Dashboard
2. Resume 或 Jobs
3. Tracker

如果你放 4 到 5 张图，建议顺序是：

1. Dashboard
2. Resume
3. Jobs
4. Interview
5. Tracker

### 截图展示小建议

- 首页截图优先展示全局导航和模块入口
- Resume / Jobs / Tracker 截图优先展示“结果区”，不要只截空表单
- 如果页面里有 AI 输出，尽量保留一段真实结果，画面会更有说服力
- GitHub 首页建议每张图只配一句话，控制在 1 到 2 行内

## 演示走查

1. 登录：使用 `demo / demo123`
2. Resume：创建或更新简历，生成摘要或优化建议
3. Jobs：查看岗位列表，执行岗位匹配
4. Interview：生成题目，提交回答并查看评估
5. Tracker：创建投递记录，生成下一步建议

## API 文档

启动后端后可直接访问：

- Swagger UI：`http://127.0.0.1:8000/docs`
- ReDoc：`http://127.0.0.1:8000/redoc`

常用接口分组如下：

- 用户：`POST /api/v1/users/`、`POST /api/v1/users/login/`、`GET /api/v1/users/me`
- 简历：`POST /api/v1/resumes/`、`PUT /api/v1/resumes/{id}`、`POST /api/v1/resumes/{id}/summary/`、`POST /api/v1/resumes/{id}/improvements/`
- 岗位：`POST /api/v1/jobs/`、`GET /api/v1/jobs/`、`POST /api/v1/jobs/{id}/match/`
- 面试：`POST /api/v1/interview/questions/generate/`、`POST /api/v1/interview/answers/evaluate/`
- 追踪：`POST /api/v1/tracker/applications/`、`POST /api/v1/tracker/applications/{id}/advice/`
- 系统：`GET /health`、`GET /ready`

## 测试

```bash
make test
make test-unit
make test-integration
make test-e2e
make test-smoke
make test-release
```

Windows 无 `make`：

```bash
scripts\run_tests.bat smoke
```

如果你只想快速确认关键链路，优先跑：

```bash
make test-smoke
```

## 项目结构

```text
src/
├── presentation/    # 路由、Schema、依赖注入、异常转换
├── business_logic/  # 业务服务、流程编排、领域逻辑
├── data_access/     # 实体、Repository、持久化访问
└── core/            # LLM、Agent、tools、memory 等跨层能力
```

依赖方向：

`presentation -> business_logic -> data_access`

`core` 是共享层，可被多个模块复用。

明确禁止：

- API 直接访问 ORM 或 Repository
- 数据层反向依赖上层
- 在路由层堆积业务逻辑

## 部署提醒

当前 Compose 更适合本地演示或预发布验证，不是可以直接替代生产部署方案的最终模板。

上线前请至少确认：

- `.env` 基于 `.env.example`
- `.env.compose` 基于 `.env.compose.example`
- `SECRET_KEY` 不是占位值
- 没有把真实生产密钥写进可提交文件
- `CORS_ORIGINS` 与目标前端域名一致
- 如果使用真实 LLM provider，相关 API Key 已正确配置
- `SEED_DEMO_ON_BOOT` 在生产环境保持关闭

## 相关文件

- 项目规则与团队：[AGENTS.md](./AGENTS.md)
- 阶段计划：[.sisyphus/plans/PLAN.md](./.sisyphus/plans/PLAN.md)
- 内部工作区：[docs/internal/](./docs/internal/)
