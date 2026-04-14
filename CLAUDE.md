# AI 实习求职 Agent 系统 — 开发规则

> 版本: v2.3.0

---

## 必读文档

- `docs/design/internship-design-document.md` — 系统设计
- `docs/design/tech-stack.md` — 技术栈

## 架构红线

- 依赖方向：`presentation -> business_logic -> infrastructure`
- API 层不得直接操作 ORM / Repository
- 前端不得直接调用 LLM
- 工具层禁止从 `presentation` 层导入

## 已实现功能

| 功能 | 状态 |
|------|------|
| JD 定制简历 | ✅ |
| AI 面试教练（多轮） | ✅ |
| 岗位匹配 | ✅ |
| Agent 助手 | ✅ |
| Docker 多环境部署 | ✅ |

## 技术栈

### 后端
- Python 3.10+ · FastAPI · SQLAlchemy 2.0 · Alembic · PostgreSQL

### 前端
- React 18 + TypeScript · Vite · TanStack Query · Zustand

### 测试
- pytest + Playwright

## 交付方式

- 一次只改一个模块
- 先改文档与边界，再改实现
- 每一步都要有验证

## 回复要求

- 强制使用中文回复

---

*版本: v2.3.0*
