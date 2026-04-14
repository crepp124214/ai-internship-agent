# AI 实习求职 Agent

> 基于多 Agent 协作的智能求职助手，帮助学生系统化准备实习申请，提升求职成功率

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18-61dafb.svg)](https://reactjs.org/)

## 核心功能

| 功能 | 说明 |
|------|------|
| 简历优化 | 上传简历，根据目标岗位 JD 生成定向优化建议（关键词匹配、技能差距分析、经历描述改进） |
| AI 面试 | 多轮对话式模拟面试，实时评分与反馈，思路引导与知识点补充 |
| 岗位匹配 | 分析简历与岗位匹配度，量化打分（0-100），生成匹配报告与改进方向 |
| Agent 助手 | 自然语言交互的智能助手，支持搜索招聘官网、分析 JD 要求 |

## 技术架构

```
ai-internship-agent/
├── backend/              # 后端 (FastAPI + DDD 架构)
│   ├── app/api/          # RESTful API
│   ├── domain/           # 领域逻辑 (Agent、面试、JD、简历、岗位)
│   └── infrastructure/   # 基础设施 (数据库、LLM 适配器)
├── frontend/             # 前端 (React 18 + TypeScript)
├── tests/               # 测试 (unit/integration/e2e)
└── docker/              # Docker 部署
```

**技术栈：**

| 层级 | 技术 |
|------|------|
| 后端 | Python · FastAPI · SQLAlchemy 2.0 · PostgreSQL · Redis |
| 前端 | React 18 · TypeScript · Vite · TanStack Query · Zustand |
| Agent | LangChain BaseTool · ReAct Loop · ToolRegistry |
| LLM | OpenAI · MiniMax · DeepSeek · 智谱AI · 通义千问 (可选) |
| 测试 | pytest · Playwright · 708 测试用例 · 80%+ 覆盖率 |

**架构亮点：**
- DDD 分层架构：清晰的领域驱动设计，应用层、领域层、基础设施层分离
- 多 Agent 协作：简历 Agent、岗位 Agent、面试 Agent 独立运行
- Agent 运行时：基于 ReAct 模式，支持工具注册、状态管理、记忆存储
- LLM 灵活配置：支持多个主流大模型，可按 Agent 单独配置

## 快速部署

**Docker 部署（推荐）：**

```bash
git clone https://github.com/crepp124214/ai-internship-agent.git
cd ai-internship-agent
docker compose -f docker/docker-compose.yml up --build
```

访问 http://localhost:3000，使用演示账号登录：

- 用户名：`demo`
- 密码：`demo123`

**本地开发：**

```bash
# 后端
pip install -r requirements.txt
python -m uvicorn backend.main:app --reload --port 8000

# 前端
cd frontend && npm install && npm run dev
```

## 配置 LLM（可选）

默认使用 Mock 模式，无需 API Key：

```env
# .env.local
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key
```

或在设置中心通过 UI 配置。

## 测试

```bash
pytest tests/ -v
```

## 项目文档

- [系统设计](docs/design/internship-design-document.md)
- [技术栈](docs/design/tech-stack.md)

## License

MIT
