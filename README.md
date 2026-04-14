# AI 实习求职 Agent

> 面向学生的智能求职助手，基于 AI Agent 技术，提供简历优化、AI模拟面试、岗位匹配等功能

## 核心功能

- **简历优化** - 上传简历，根据目标岗位生成定向优化建议
- **AI 面试** - 多轮对话式模拟面试，实时评分与反馈
- **岗位匹配** - 分析简历与岗位匹配度，量化打分
- **Agent 助手** - 自然语言交互的智能求职助手

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

## 本地开发

```bash
# 后端
pip install -r requirements.txt
python -m uvicorn backend.main:app --reload --port 8000

# 前端
cd frontend && npm install && npm run dev
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python · FastAPI · SQLAlchemy · PostgreSQL |
| 前端 | React 18 · TypeScript · Vite · TanStack Query |
| Agent | LangChain · ReAct · ToolRegistry |
| LLM | OpenAI · MiniMax · DeepSeek · 智谱AI (可选) |

## 配置 LLM（可选）

默认使用 Mock 模式，无需 API Key。如需真实 AI 能力：

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

## 文档

- [系统设计](docs/design/internship-design-document.md)
- [技术栈](docs/design/tech-stack.md)

## License

MIT
