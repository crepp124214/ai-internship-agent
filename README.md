# AI 实习求职 Agent 系统

围绕实习求职流程的 Python 后端 + React 前端项目，目标是可运行、可演示、可验证、可维护。

## 快速开始

```bash
# 后端
cp .env.example .env
cp frontend/.env.example frontend/.env
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
python scripts/migrate.py
python scripts/seed_demo.py
make dev

# 前端（新终端）
cd frontend
npm install
npm run dev
```

后端默认 `http://127.0.0.1:8000`，前端默认 `http://127.0.0.1:5173`。

演示账号：`demo / demo123`

## 产品

围绕四条业务线提供 AI 辅助能力：

| 页面 | 能力 |
|---|---|
| `/resume` | 简历管理、AI 摘要、优化建议、历史记录 |
| `/jobs` | 岗位管理、匹配评估、历史记录 |
| `/interview` | 面试题生成、回答评估、记录 |
| `/tracker` | 投递追踪、下一步建议、历史记录 |

所有"建议类能力"都区分**即时预览**与**持久化**。

## 架构

三层架构 + 公共核心层：

```text
src/
├── presentation/    # 路由、Schema、依赖注入、异常转换
├── business_logic/  # 业务服务、流程编排、领域逻辑
├── data_access/     # 实体、Repository、持久化访问
└── core/            # LLM、Agent、tools、memory 等跨层能力
```

依赖方向：`presentation -> business_logic -> data_access`，`core` 作为共享层。

禁止：API 直接访问 ORM/Repository、数据层反向依赖上层、在路由层堆积业务逻辑。

## API 文档

启动后端后自动生成：

- Swagger UI：`http://127.0.0.1:8000/docs`
- ReDoc：`http://127.0.0.1:8000/redoc`

常用接口：

- 用户：`POST /api/v1/users/`、`POST /api/v1/users/login/`、`GET /api/v1/users/me`
- 简历：`POST /api/v1/resumes/`、`PUT /api/v1/resumes/{id}`、`POST /api/v1/resumes/{id}/summary/`、`POST /api/v1/resumes/{id}/improvements/`
- 岗位：`POST /api/v1/jobs/`、`GET /api/v1/jobs/`、`POST /api/v1/jobs/{id}/match/`
- 面试：`POST /api/v1/interview/questions/generate/`、`POST /api/v1/interview/answers/evaluate/`
- 追踪：`POST /api/v1/tracker/applications/`、`POST /api/v1/tracker/applications/{id}/advice/`
- 系统：`GET /health`、`GET /ready`

## 测试

```bash
make test              # 全量测试
make test-unit         # 单元测试
make test-integration  # 集成测试
make test-e2e          # 端到端测试
make test-smoke        # 快速冒烟测试
make test-release      # 发布就绪验证
```

Windows 无 `make`：`scripts\run_tests.bat smoke`

## 部署

```bash
# Docker Compose
cp .env.example .env
make compose-up

# 等价
docker compose -f docker/docker-compose.yml up --build
```

发布前检查：

- `.env` 基于 `.env.example`，`SECRET_KEY` 非占位值
- `LLM_PROVIDER` 是有意选择，使用真实 provider 时 API Key 已配置
- `CORS_ORIGINS` 与目标前端域名一致
- `GET /health` 和 `GET /ready` 返回 200
- `make test-smoke` 和 `make test-release` 通过

## 演示走查

1. 登录（`demo / demo123`）
2. Dashboard → 查看当前进展
3. Resume → 创建/更新/生成摘要
4. Jobs → 浏览岗位/匹配评估
5. Interview → 生成题目/评估回答
6. Tracker → 跟踪投递/生成建议

最小验收：`/health = 200`、`/ready = 200`、登录后受保护路径可访问。

## 提交前检查

- 改动是否遵守三层边界
- 是否补了必要测试
- 是否更新了阶段文档

## 其他文件

- 项目规则与团队：[AGENTS.md](./AGENTS.md)
- 阶段计划：[.sisyphus/plans/PLAN.md](./.sisyphus/plans/PLAN.md)
- 内部工作区：[docs/internal/](./docs/internal/)（设计稿、Agent 提示词、决策记录）
