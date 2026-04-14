# AI 实习求职 Agent

> 🎯 基于多 Agent 协作的智能求职助手，帮助学生系统化准备实习申请，提升求职成功率

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18-61dafb.svg)](https://reactjs.org/)

**AI 实习求职 Agent** 是一款面向求职学生的 AI 助手产品，通过 **简历定制优化**、**AI 模拟面试**、**岗位智能匹配** 等功能，解决学生在求职过程中遇到的简历撰写、面试准备、岗位筛选等痛点问题。

---

## 🔗 相关链接

### 📚 文档资源
- [📖 完整文档索引](docs/README.md) - 架构设计、API 文档、开发指南
- [📊 测试与质量报告](docs/reports/complete-test-analysis-report.md) - 708 个测试用例，80%+ 覆盖率
- [🏗️ 项目结构重构报告](docs/reports/refactor-report-2026-04-12.md) - DDD 架构迁移记录
- [👨‍💻 开发规则](CLAUDE.md) - 架构约束、技术栈、开发规范

---

## 🚀 快速开始

### 🐳 方式一：Docker 一键部署（推荐）

> 💡 **适用场景**：第一次运行、想要最快速度体验、不想配置环境

#### 步骤 1：检查 Docker 环境

确认已安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)

```bash
docker --version
# 应显示版本号，如：Docker version 24.0.0 ✅
```

#### 步骤 2：启动服务

```bash
# 克隆项目
git clone <repository-url>
cd ai-internship-agent

# 一键启动所有服务
docker compose -f docker/docker-compose.yml up --build
```

> ⏳ **首次运行**：需要下载镜像，约 3-5 分钟

#### 步骤 3：访问服务

| 服务 | 地址 | 说明 |
|------|------|------|
| 🌐 前端应用 | http://localhost:3000 | 用户界面 |
| 🔌 后端 API | http://localhost:8000 | RESTful API |
| 📚 API 文档 | http://localhost:8000/docs | Swagger UI |

#### 步骤 4：登录体验

演示账号已自动创建：

```
用户名：demo
密码：demo123
```

**登录后即可体验**：
- ✅ 岗位探索：导入或创建岗位，收藏到岗位库
- ✅ 简历优化：从岗位探索带入岗位信息，进行 JD 定向优化
- ✅ 面试准备：生成面试题目或开始 AI 面试教练对练
- ✅ 设置中心：查看简历、岗位、面试记录管理，配置 Agent

> 💡 **演示模式 vs 生产模式**：
> - **演示模式**（默认）：使用 mock LLM，不需要 API 密钥即可体验核心流程
> - **生产模式**：配置真实 API Key 后，AI 功能由真实大模型驱动
> 
> 📋 **切换到生产模式**：参见 [docker/README.md](docker/README.md)

---

### 👨‍💻 方式二：本地开发部署

> 💡 **适用场景**：想要修改代码、进行开发、需要接入真实 LLM

<details>
<summary><b>📋 展开查看详细步骤</b></summary>

#### 步骤 1：检查环境依赖

| 软件 | 版本要求 | 安装地址 |
|------|----------|----------|
| Python | 3.10+ | [python.org](https://www.python.org/downloads/) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org/) |
| PostgreSQL | 15+ | [postgresql.org](https://www.postgresql.org/download/) |
| Redis | 7+ | [redis.io](https://redis.io/download/) |

验证安装：
```bash
python --version    # Python 3.10.x 或更高 ✅
node --version      # v18.x.x 或更高 ✅
psql --version      # psql (PostgreSQL) 15.x ✅
```

#### 步骤 2：安装依赖

```bash
# 后端依赖
pip install -r requirements.txt -r requirements-dev.txt

# 前端依赖
cd frontend
npm install
cd ..
```

#### 步骤 3：配置环境变量

```bash
# 复制配置文件
cp .env.local.example .env.local
```

编辑 `.env.local`，修改数据库连接：
```env
DATABASE_URL=postgresql+psycopg://postgres:你的密码@localhost:5432/postgres
```

#### 步骤 4：初始化数据库

```bash
# 启动 PostgreSQL 和 Redis 服务
# Windows: 在"服务"应用中启动
# Mac: brew services start postgresql@15 && brew services start redis
# Linux: sudo systemctl start postgresql && sudo systemctl start redis

# 创建数据库
psql -U postgres -c "CREATE DATABASE internship_agent;"

# 运行迁移
python -m alembic upgrade head

# 导入演示数据（可选）
python scripts/seed_demo.py
```

#### 步骤 5：启动服务

**启动后端**（新终端窗口）：
```bash
APP_ENV=development DATABASE_URL=sqlite:///./data/app.db \
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**启动前端**（新终端窗口）：
```bash
cd frontend
npm run dev
```

#### 步骤 6：访问应用

打开浏览器访问：http://localhost:5173

使用演示账号登录：`demo` / `demo123`

</details>

---

## ⏳ 核心功能

- [x] **简历定制** - 上传简历，根据目标岗位（JD）生成针对性的优化建议
  - 关键词提取与匹配
  - 技能差距分析
  - 经历描述改进建议
  
- [x] **AI 模拟面试** - 基于简历和目标岗位，生成个性化面试题库
  - 多轮对话式练习
  - 实时评分与改进建议
  - 思路引导与知识点补充
  
- [x] **岗位匹配** - 分析简历与岗位的匹配度
  - 量化打分（0-100）
  - 匹配度可视化
  - 差距分析与改进方向
  
- [x] **Agent 助手** - 自然语言交互的智能助手
  - 搜索公司招聘官网
  - 分析 JD 要求
  - 回答求职相关问题

- [ ] **岗位推荐** - 基于简历自动推荐匹配岗位（规划中）
- [ ] **求职进度管理** - 跟踪申请状态和面试安排（规划中）

---

## 🏗️ 技术架构

### 技术栈

| 层级 | 技术 |
|------|------|
| **后端** | Python · FastAPI · SQLAlchemy 2.0 · PostgreSQL · Redis |
| **前端** | React 18 · TypeScript · Vite · TanStack Query · Zustand |
| **Agent** | LangChain BaseTool · ReAct Loop · ToolRegistry |
| **LLM** | OpenAI · Anthropic · MiniMax · DeepSeek · 智谱 AI · 通义千问 · Moonshot · SiliconFlow |
| **测试** | pytest · Playwright · 708 测试用例 · 80%+ 覆盖率 |
| **部署** | Docker · Docker Compose · GitHub Actions |

### 架构亮点

- 🏛️ **DDD 分层架构** - 清晰的领域驱动设计，应用层、领域层、基础设施层分离
- 🤖 **多 Agent 协作** - 简历 Agent、岗位 Agent、面试 Agent 独立运行，各自专注垂直场景
- 🔧 **Agent 运行时** - 基于 ReAct 模式的 Agent 运行时，支持工具注册、状态管理、记忆存储
- 🔌 **LLM 灵活配置** - 支持 8 个主流大模型，可按 Agent 单独配置，支持 Mock 模式
- 🎨 **前后端分离** - RESTful API 设计，前后端独立开发部署

### 项目结构

```
ai-internship-agent/
├── backend/                      # 后端代码（DDD 架构）
│   ├── app/                     # 应用层
│   │   └── api/v1/             # RESTful API 端点
│   ├── domain/                  # 领域层
│   │   ├── agent/              # Agent 运行时与助手服务
│   │   ├── interview/          # 面试模块（教练、会话管理）
│   │   ├── jd/                # JD 定制模块
│   │   ├── job/               # 岗位模块
│   │   └── resume/            # 简历模块
│   ├── infrastructure/          # 基础设施层
│   │   ├── database/           # 数据库实体和仓库
│   │   └── llm/               # LLM 适配器（OpenAI、Minimax 等）
│   └── shared/                 # 共享能力
│       ├── runtime/           # Agent Runtime（Executor、StateMachine）
│       ├── tools/            # 基础工具（搜索、解析等）
│       ├── errors/           # 异常处理
│       └── tracing/          # 链路追踪
├── frontend/                    # 前端代码
│   └── src/
│       ├── pages/             # 页面组件（仪表盘、岗位、简历、面试）
│       ├── components/        # 可复用组件
│       ├── hooks/            # React Hooks
│       └── lib/              # 工具库（API 客户端、状态管理）
├── tests/                      # 测试代码
│   ├── unit/                 # 单元测试
│   ├── integration/          # 集成测试
│   └── e2e/                  # 端到端测试
├── docker/                     # Docker 配置
├── alembic/                    # 数据库迁移
└── docs/                       # 文档
```

---

## ⚙️ 环境变量配置

### 📁 配置文件说明

| 文件 | 用途 | 优先级 |
|------|------|--------|
| `.env.local` | 本地开发配置 | 最高 |
| `.env.development` | 开发环境配置 | 中 |
| `.env.production` | 生产环境配置 | 中 |
| `.env` | 默认配置 | 最低 |

### 🔧 快速配置

<details>
<summary><b>🔐 安全配置（重要）</b></summary>

```env
# JWT 密钥（生产环境必须修改）
SECRET_KEY=your-secret-key-here

# 数据库连接
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/dbname

# Redis 连接
REDIS_URL=redis://localhost:6379/0
```

</details>

<details>
<summary><b>🤖 LLM 配置</b></summary>

```env
# LLM 提供商（openai/minimax/deepseek/zhipu/qwen/moonshot/siliconflow）
LLM_PROVIDER=openai

# OpenAI 配置
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4

# Minimax 配置
MINIMAX_API_KEY=...
MINIMAX_MODEL=abab6.5-chat

# 智谱 AI 配置
ZHIPU_API_KEY=...
ZHIPU_MODEL=glm-4

# DeepSeek 配置
DEEPSEEK_API_KEY=...
DEEPSEEK_MODEL=deepseek-chat
```

> 💡 **提示**：也可以在设置中心通过 UI 界面配置，优先级高于环境变量

</details>

<details>
<summary><b>🌐 CORS 配置</b></summary>

```env
# 允许的跨域来源（逗号分隔）
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

</details>

<details>
<summary><b>🛡️ 速率限制</b></summary>

```env
# 速率限制配置
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60
```

</details>

---

## 📖 API 文档

启动后访问 Swagger UI：http://localhost:8000/docs

### 常用接口示例

<details>
<summary><b>🔑 用户认证</b></summary>

```bash
# 登录
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo123"}'

# 响应
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

</details>

<details>
<summary><b>📄 简历管理</b></summary>

```bash
# 获取简历列表
curl http://localhost:8000/api/v1/resumes/ \
  -H "Authorization: Bearer <TOKEN>"

# 上传简历
curl -X POST http://localhost:8000/api/v1/resumes/ \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"title":"我的简历","content":"..."}'
```

</details>

<details>
<summary><b>💼 岗位管理</b></summary>

```bash
# 获取岗位列表
curl http://localhost:8000/api/v1/jobs/ \
  -H "Authorization: Bearer <TOKEN>"

# 创建岗位
curl -X POST http://localhost:8000/api/v1/jobs/ \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"title":"前端开发实习生","company":"字节跳动","jd":"..."}'
```

</details>

<details>
<summary><b>🎤 面试管理</b></summary>

```bash
# 开始面试会话
curl -X POST http://localhost:8000/api/v1/interviews/sessions \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"resume_id":1,"job_id":2}'

# 发送面试消息
curl -X POST http://localhost:8000/api/v1/interviews/sessions/1/messages \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"content":"我的项目经验是..."}'
```

</details>

---

## 🧪 测试

```bash
# 运行所有测试（708 个测试用例）
pytest

# 单元测试
pytest tests/unit -v

# 集成测试
pytest tests/integration -v

# E2E 测试（需要启动前后端服务）
pytest tests/e2e -v

# 生成覆盖率报告
pytest --cov=backend --cov-report=html
```

**测试统计**：
- ✅ 708 个测试用例全部通过
- 📊 代码覆盖率：80.39%
- ⚡ 执行时间：约 4 分钟

详细测试报告：[complete-test-analysis-report.md](docs/reports/complete-test-analysis-report.md)

---

## ❓ 常见问题

<details>
<summary><b>Q: Docker 启动失败，显示端口被占用？</b></summary>

```bash
# 查看哪个进程占用了端口
netstat -ano | findstr :5432   # PostgreSQL
netstat -ano | findstr :6379    # Redis
netstat -ano | findstr :3000    # 前端
```

**解决方案**：
1. 关闭占用端口的程序
2. 或修改 `docker/docker-compose.yml` 中的端口映射

</details>

<details>
<summary><b>Q: 登录失败，提示用户不存在？</b></summary>

运行以下命令创建演示账号：
```bash
python scripts/seed_demo.py
```

</details>

<details>
<summary><b>Q: 后端启动报错 "connection refused"？</b></summary>

**检查清单**：
1. PostgreSQL 和 Redis 是否已启动
2. `.env.local` 中的 `DATABASE_URL` 密码是否正确
3. 防火墙是否阻止了连接

</details>

<details>
<summary><b>Q: 前端页面空白？</b></summary>

**解决方案**：
1. 按 `Ctrl+F5` 强制刷新清除缓存
2. 检查浏览器控制台是否有错误
3. 确认后端 API 是否正常运行

</details>

<details>
<summary><b>Q: AI 功能返回 Mock 数据？</b></summary>

**原因**：未配置真实 LLM API Key

**解决方案**：
1. 在 `.env.local` 中配置 LLM API Key
2. 或在设置中心通过 UI 界面配置
3. 重启后端服务

</details>

<details>
<summary><b>Q: 如何切换不同的 LLM 提供商？</b></summary>

**方式一：环境变量**
```env
LLM_PROVIDER=minimax
MINIMAX_API_KEY=your-key
MINIMAX_MODEL=abab6.5-chat
```

**方式二：设置中心**
1. 登录后进入"设置中心"
2. 选择"Agent 配置"
3. 为不同 Agent 配置不同的 LLM

</details>

---

## 📚 相关文档

| 文档 | 说明 |
|------|------|
| [📖 完整文档索引](docs/README.md) | 所有文档的导航中心 |
| [👨‍💻 开发规则](CLAUDE.md) | 架构约束、技术栈、开发规范 |
| [📊 测试报告](docs/reports/complete-test-analysis-report.md) | 708 个测试用例，80%+ 覆盖率 |
| [🏗️ 重构报告](docs/reports/refactor-report-2026-04-12.md) | DDD 架构迁移记录 |
| [🤝 贡献指南](CONTRIBUTING.md) | 如何参与项目开发 |
| [🐳 Docker 部署](docker/README.md) | Docker 部署详细说明 |

---

## 📄 License

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者！

如果这个项目对你有帮助，欢迎 ⭐ Star 支持一下！
