# 用户 LLM 配置功能设计

> 日期：2026-04-08 | 状态：草稿

## 背景

允许用户自己接入各家的 LLM API（OpenAI / Anthropic 兼容），自己带 Key 自己用，互不干扰。

## 核心设计

### 数据库模型

**表：`user_llm_configs`**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer, PK | 主键 |
| user_id | Integer, FK | 用户外键 |
| agent | String(50) | resume_agent / job_agent / interview_agent |
| provider | String(100) | 支持自定义填入（任意兼容 API 的 provider 标识） |
| model | String(100) | 模型名称，如 gpt-4o-mini |
| api_key_encrypted | String(500) | 加密后的 API Key |
| base_url | String(255), nullable | 可选，自定义 endpoint |
| temperature | Float, nullable | 生成温度，默认 0.7 |
| is_active | Boolean | 是否启用，默认 True |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

**约束：** (user_id, agent) 唯一，每个用户每个 Agent 只有一条配置。

### API 设计

**Base Path:** `/api/v1/users/llm-configs`

| Method | Path | 说明 |
|--------|------|------|
| GET | / | 获取当前用户所有 Agent 配置 |
| POST | / | 创建或更新某个 Agent 的配置 |
| DELETE | /{agent} | 删除某个 Agent 的配置（回退到系统默认） |

**Request Body（POST）:**
```json
{
  "agent": "resume_agent",
  "provider": "openai",
  "model": "gpt-4o-mini",
  "api_key": "sk-...",
  "base_url": null,
  "temperature": 0.7
}
```

**Response:**
```json
{
  "agent": "resume_agent",
  "provider": "openai",
  "model": "gpt-4o-mini",
  "base_url": null,
  "temperature": 0.7,
  "is_active": true,
  "updated_at": "2026-04-08T..."
}
```

**注意：** API Key 在后端加密存储，前端不会回显。

### Agent 运行时集成

1. Agent 执行前，通过 `user_id` + `agent_name` 查询 `user_llm_configs`
2. 如果存在且 `is_active=True`，使用用户配置构建 LLM Adapter
3. 如果不存在，回退到系统默认配置（环境变量 / settings.yaml）

**优先级：** 用户配置 > 系统默认

### 前端页面

**路由：** `/settings/agent-config`（或放在 `/settings` 下 Tab）

**布局：** 三个 Agent 卡片（简历 Agent / 岗位 Agent / 面试 Agent），每个卡片显示当前配置的 Provider + Model，点击编辑展开表单。

**表单字段：**
- Provider（可选择也可自定义填入，下拉包含常用选项：OpenAI / Anthropic / MiniMax / DeepSeek / 智谱 / 通义 / Moonshot / SiliconFlow，也支持手动输入其他兼容 OpenAI API 的 provider）
- API Key（密码输入，加密传输）
- Model（根据 Provider 联动，可选可填）
- Base URL（非必填）
- Temperature（滑块 0-2，默认 0.7）
- 保存按钮

**交互：** 保存后立即生效，无需重启服务。

## 技术实现

### 后端

- 新建 `src/data_access/entities/user_llm_config.py` — SQLAlchemy 模型
- 新建 `src/data_access/repositories/user_llm_config_repository.py` — Repository
- 新建 `src/presentation/api/v1/user_llm_configs.py` — CRUD API
- 新建 `src/presentation/schemas/user_llm_config.py` — Pydantic Schema
- 修改 `src/business_logic/agents/*/agent.py` — 查询用户配置，优先使用
- API Key 使用 Fernet 对称加密存储

### 前端

- 新建 `frontend/src/pages/settings/agent-config-page.tsx` — 配置页面
- 在侧边栏设置入口（`authenticated-app-shell.tsx`）
- 使用 React Hook Form + Zod 验证
- API 调用通过 `src/lib/api.ts` 扩展

## Provider 支持

### OpenAI 兼容（/v1/chat/completions）

| Provider | Base URL |
|----------|----------|
| OpenAI | https://api.openai.com/v1 |
| MiniMax | https://api.minimax.chat/v1 |
| DeepSeek | https://api.deepseek.com/v1 |
| 智谱 | https://open.bigmodel.cn/api/paas/v4 |
| 通义 | https://dashscope.aliyuncs.com/compatible-mode/v1 |
| Moonshot | https://api.moonshot.cn/v1 |
| SiliconFlow | https://api.siliconflow.cn/v1 |

### Anthropic 兼容（/v1/messages）

| Provider | Base URL |
|----------|----------|
| Anthropic | https://api.anthropic.com/v1 |

## 安全

- API Key 加密存储（Fernet / AES），不可逆泄露
- 用户只能读写自己的配置
- DELETE 操作软删除（is_active=False）或物理删除

## 验证清单

- [ ] 用户 A 配置的 Key 不会影响用户 B
- [ ] API Key 明文不在 Response 中返回
- [ ] 不配置时 Agent 正常回退到系统默认
- [ ] 前端 Provider 切换后 Model 字段正确联动
