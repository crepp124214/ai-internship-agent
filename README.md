# AI 实习求职 Agent

一款面向求职学生的 AI 助手产品，帮助用户系统化准备实习申请，提升求职成功率。

## 背景

找实习是求职的第一步，但大多数学生面临以下困境：

- **简历不知道怎么写** — 不知道 HR 看重什么经历，不知道如何针对不同岗位调整简历
- **面试不知道考什么** — 准备方向不明确，刷题效率低，模拟面试资源有限
- **岗位信息分散** — 需要在多个平台搜索，信息整合耗时耗力
- **缺乏反馈机制** — 不知道自己简历写得怎么样，面试回答得好不好

本项目旨在解决这些问题，通过 AI 技术提供 **简历定制优化**、**AI 模拟面试**、**岗位智能匹配** 等功能，帮助学生更有针对性地准备求职。

## 核心功能

| 功能 | 说明 |
|------|------|
| 简历定制 | 上传简历，根据目标岗位（JD）生成针对性的优化建议，包括关键词提取、技能匹配、经历描述改进 |
| AI 模拟面试 | 基于简历和目标岗位，生成个性化面试题库。支持多轮对话式练习，实时评分、改进建议、思路引导 |
| 岗位匹配 | 分析简历与岗位的匹配度，量化打分，指出简历中与岗位要求不匹配的地方 |
| Agent 助手 | 自然语言交互的智能助手，可搜索公司招聘官网、分析 JD、回答求职相关问题 |

## 技术亮点

- **Agent 运行时架构** — 基于 ReAct 模式的 Agent 运行时，支持工具注册、状态管理、记忆存储
- **多 Agent 协作** — 简历 Agent、岗位 Agent、面试 Agent 独立运行，各自专注垂直场景
- **LLM 灵活配置** — 支持 OpenAI、MiniMax、DeepSeek、智谱 AI 等多个大模型，可按 Agent 单独配置
- **前后端分离** — 前端 React + TypeScript，后端 FastAPI + SQLAlchemy，架构清晰易于扩展

| 功能 | 说明 |
|------|------|
| 简历定制 | 上传简历，根据目标岗位生成优化建议 |
| AI 模拟面试 | 多轮对话面试，实时评分和改进建议 |
| 岗位匹配 | 分析简历与岗位的匹配度 |
| Agent 助手 | 智能助手面板，支持自然语言交互 |

---

## 快速开始

### 方式一：Docker 部署（推荐）

**适用场景**：第一次运行、想要最快速度体验、不想配置环境

#### 第一步：检查环境

确认已安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)（Windows 用户）

打开终端，运行：
```bash
docker --version
```
如果显示版本号，说明 Docker 已安装。

#### 第二步：启动服务

在项目根目录打开终端，运行：

```bash
docker compose -f docker/docker-compose.yml up --build
```

**耐心等待**：首次运行需要下载镜像（约 3-5 分钟）

#### 第三步：访问应用

打开浏览器，访问：**http://localhost:3000**

> 如果 port 3000 被占用，docker-compose 可能自动切换到其他端口。观察启动日志中的 `localhost:xxxx` 地址。

看到登录页面就成功了！

#### 第四步：登录体验

演示账号已自动创建：
- **用户名**：`demo`
- **密码**：`demo123`

---

### 方式二：本地开发

**适用场景**：想要修改代码、进行开发、需要 API 接入真实 LLM

#### 第一步：检查环境

确认已安装以下软件：

| 软件 | 版本要求 | 安装地址 |
|------|----------|----------|
| Python | 3.10+ | [python.org](https://www.python.org/downloads/) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org/) |
| PostgreSQL | 15+ | [postgresql.org](https://www.postgresql.org/download/) |
| Redis | 7+ | [redis.io](https://redis.io/download/) |

验证安装（打开终端/命令提示符）：
```bash
python --version    # 应显示 Python 3.10.x 或更高
node --version      # 应显示 v18.x.x 或更高
psql --version     # 应显示 psql (PostgreSQL) 15.x
```

#### 第二步：克隆项目

```bash
git clone <repository-url>
cd ai-internship-agent
```

#### 第三步：安装后端依赖

在项目根目录打开终端，运行：

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

**如果遇到问题**：
- Windows 用户可能需要使用 `pip3`
- 某些包安装失败？尝试 `pip install --no-cache-dir -r requirements.txt`
- 提示 "Microsoft Visual C++ Build Tools"？去 https://visualstudio.microsoft.com/visual-cpp-build-tools/ 下载安装

#### 第四步：配置环境变量

复制配置文件：

```bash
cp .env.local.example .env.local
```

用文本编辑器打开 `.env.local` 文件，修改数据库连接：

```
DATABASE_URL=postgresql://postgres:你的密码@localhost:5432/postgres
```

> **注意**：把"你的密码"改成你安装 PostgreSQL 时设置的密码。如果没改过，Windows 默认可能是 `postgres`，Mac/Linux 默认可能是你的用户名。

#### 第五步：启动数据库服务

**Windows 用户**：
1. 打开"服务"应用（搜索"服务"）
2. 找到 "postgresql-x64-15"（数字可能不同）
3. 点击"启动"

**Mac 用户**：
```bash
brew services start postgresql@15
```

**Linux 用户**：
```bash
sudo systemctl start postgresql
```

同样启动 Redis：
- Windows：Redis 在 WSL 或 Docker 中运行较方便
- Mac：`brew services start redis`
- Linux：`sudo systemctl start redis`

#### 第六步：创建数据库

连接到 PostgreSQL，创建数据库：

```bash
psql -U postgres
```

在 psql 终端中运行：

```sql
CREATE DATABASE internship_agent;
\q
```

#### 第七步：初始化数据库

在项目根目录运行：

```bash
python -m alembic upgrade head
```

**成功标志**：显示 "Running upgrade ... -> xxx"

#### 第八步：导入演示数据（可选）

```bash
python scripts/seed_demo.py
```

这会创建演示账号和样例数据。

#### 第九步：启动后端

新开一个终端窗口：

```bash
cd ai-internship-agent
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

**成功标志**：显示 `Uvicorn running on http://0.0.0.0:8000`

#### 第十步：启动前端

再新开一个终端窗口：

```bash
cd ai-internship-agent/frontend
npm install
npm run dev
```

**成功标志**：显示 `VITE v8.0.3 ready in xxx ms`

#### 第十一步：访问应用

打开浏览器，访问终端显示的地址（通常是 **http://localhost:5173**）

看到登录页面即成功！

#### 第十二步：登录体验

- **用户名**：`demo`
- **密码**：`demo123`

---

## 项目结构

```
ai-internship-agent/
├── src/                          # 后端代码
│   ├── business_logic/            # 业务逻辑
│   │   ├── agent/               # Agent 运行时
│   │   ├── interview/           # 面试模块
│   │   ├── jd/                 # JD 定制模块
│   │   └── job/                # 岗位模块
│   ├── core/                    # 核心能力
│   │   ├── runtime/            # Agent Runtime（Executor, StateMachine）
│   │   ├── tools/             # 基础工具
│   │   └── llm/              # LLM 适配器
│   ├── data_access/           # 数据访问层
│   │   ├── entities/         # SQLAlchemy 实体
│   │   └── repositories/     # 数据仓库
│   └── presentation/         # 展示层
│       └── api/v1/          # API 端点
├── frontend/                  # 前端代码
│   └── src/
│       ├── pages/           # 页面组件
│       ├── components/      # 可复用组件
│       └── hooks/          # React Hooks
└── docker/                  # Docker 配置
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python · FastAPI · SQLAlchemy 2.0 · PostgreSQL · Redis |
| 前端 | React 18 · TypeScript · Vite · TanStack Query · Zustand |
| Agent | LangChain BaseTool · ReAct Loop · ToolRegistry |
| 测试 | pytest · Playwright |

## API 文档

启动后访问 `http://localhost:8000/docs`（Swagger UI）

### 常用接口

```bash
# 登录
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo123"}'

# 获取简历列表
curl http://localhost:8000/api/v1/resumes/ \
  -H "Authorization: Bearer <TOKEN>"

# 获取岗位列表
curl http://localhost:8000/api/v1/jobs/ \
  -H "Authorization: Bearer <TOKEN>"
```

## 测试

```bash
# 所有测试
pytest

# 单元测试
pytest tests/unit -v

# E2E 测试
pytest tests/e2e -v
```

## 常见问题

**Q: Docker 启动失败，显示端口被占用？**
```bash
# 查看哪个进程占用了端口
netstat -ano | findstr :5432   # PostgreSQL
netstat -ano | findstr :6379    # Redis
netstat -ano | findstr :3000    # 前端
```
关闭占用端口的程序，或修改 docker-compose.yml 中的端口映射。

**Q: 登录失败，提示用户不存在？**
运行 `python scripts/seed_demo.py` 创建演示账号。

**Q: 后端启动报错 "connection refused"？**
检查 PostgreSQL 和 Redis 是否已启动，并确认 `.env.local` 中的 `DATABASE_URL` 密码正确。

**Q: 前端页面空白？**
按 `Ctrl+F5` 强制刷新清除缓存。

## 相关文档

- [CLAUDE.md](CLAUDE.md) — 开发规则和架构说明
- [CONTRIBUTING.md](CONTRIBUTING.md) — 贡献指南
- [docker/README.md](docker/README.md) — Docker 部署详情

## License

MIT
