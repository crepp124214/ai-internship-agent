# API 参考概要

本文件提供对主要 API 端点的详细请求/响应示例。完整的 OpenAPI 参考请访问 `/docs`（Swagger UI）或 `/redoc`（ReDoc）。

> **默认基础 URL**: `http://127.0.0.1:8000`（本地开发）  
> **认证方式**: Bearer Token（JWT），在请求头中传递 `Authorization: Bearer <access_token>`  
> **演示用户**: `demo / demo123`

---

## 目录

1. [认证](#1-认证)
2. [简历](#2-简历)
3. [岗位](#3-岗位)
4. [面试](#4-面试)
5. [投递追踪](#5-投递追踪)
6. [健康检查](#6-健康检查)
7. [Rate Limiting](#7-rate-limiting)

---

## 1. 认证

### 1.1 登录

**请求**
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "demo",
  "password": "demo123"
}
```

**响应（200）**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**错误响应（401）**
```json
{
  "detail": "Invalid credentials"
}
```

---

### 1.2 刷新令牌

当 `access_token` 过期时（401），使用 `refresh_token` 获取新令牌。

**请求**
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**响应（200）**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### 1.3 登出

**请求**
```http
POST /api/v1/auth/logout
Authorization: Bearer <access_token>
```

**响应（200）**
```json
{
  "msg": "Refresh token revoked"
}
```

---

### 1.4 获取当前用户

**请求**
```http
GET /api/v1/users/me
Authorization: Bearer <access_token>
```

**响应（200）**
```json
{
  "id": 1,
  "username": "demo",
  "email": "demo@example.com",
  "name": "Demo User",
  "is_active": true,
  "is_verified": false,
  "created_at": "2026-01-01T00:00:00",
  "updated_at": "2026-01-01T00:00:00"
}
```

---

## 2. 简历

### 2.1 列出简历

**请求**
```http
GET /api/v1/resumes/
Authorization: Bearer <access_token>
```

**响应（200）**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "title": "2026 届实习求职主简历",
    "original_file_path": "manual/1735689600000-2026-届实习求职主简历.txt",
    "file_name": "2026-届实习求职主简历.txt",
    "file_type": "txt",
    "file_size": 2048,
    "processed_content": "张三 | 后端开发实习生...\n教育背景：...",
    "resume_text": "张三 | 后端开发实习生...\n教育背景：...",
    "language": "zh",
    "is_default": true,
    "created_at": "2026-01-15T10:30:00",
    "updated_at": "2026-01-15T10:30:00"
  }
]
```

---

### 2.2 创建简历

**请求**
```http
POST /api/v1/resumes/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "我的新简历",
  "file_path": "manual/1234567890-my-resume.txt"
}
```

**响应（200）**
```json
{
  "id": 2,
  "user_id": 1,
  "title": "我的新简历",
  "original_file_path": "manual/1234567890-my-resume.txt",
  "file_name": "my-resume.txt",
  "file_type": "txt",
  "file_size": null,
  "processed_content": null,
  "resume_text": null,
  "language": "zh",
  "is_default": false,
  "created_at": "2026-04-01T12:00:00",
  "updated_at": "2026-04-01T12:00:00"
}
```

---

### 2.3 更新简历内容

**请求**
```http
PUT /api/v1/resumes/1
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "更新后的简历标题",
  "resume_text": "张三\n后端开发实习生\n...\n教育背景：清华大学 计算机科学 2024-现在",
  "processed_content": "张三\n后端开发实习生\n...\n教育背景：清华大学 计算机科学 2024-现在",
  "is_default": true
}
```

**响应（200）**: 返回更新后的简历对象（同 2.1 格式）

---

### 2.4 生成简历摘要（预览）

**请求**
```http
POST /api/v1/resumes/1/summary/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "target_role": "后端开发实习生"
}
```

**响应（200）**
```json
{
  "mode": "summary",
  "resume_id": 1,
  "target_role": "后端开发实习生",
  "content": "该简历的主人是一名计算机专业的学生...\n主要技能包括 Python、FastAPI、数据库设计...",
  "raw_content": "mock-generate: <short assessment>\n<Task>\nSummarize this resume...",
  "provider": "mock",
  "model": "mock-model"
}
```

---

### 2.5 保存简历摘要（持久化）

**请求**
```http
POST /api/v1/resumes/1/summary/persist/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "target_role": "后端开发实习生"
}
```

**响应（200）**
```json
{
  "id": 1,
  "resume_id": 1,
  "original_text": "张三 | 后端开发实习生...",
  "optimized_text": "该简历的主人是一名计算机专业的学生...\n主要技能包括 Python、FastAPI、数据库设计...",
  "mode": "resume_summary",
  "keywords": null,
  "score": null,
  "ai_suggestion": null,
  "raw_content": "mock-generate: <short assessment>...",
  "provider": "mock",
  "model": "mock-model",
  "created_at": "2026-04-01T12:05:00",
  "updated_at": "2026-04-01T12:05:00"
}
```

---

### 2.6 生成简历优化建议（预览）

**请求**
```http
POST /api/v1/resumes/1/improvements/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "target_role": "后端开发实习生"
}
```

**响应（200）**
```json
{
  "mode": "improvements",
  "resume_id": 1,
  "target_role": "后端开发实习生",
  "content": "1. 建议在技能部分突出 FastAPI 和异步编程经验...\n2. 项目经验描述中建议加入具体技术栈...",
  "raw_content": "mock-generate: <one concise paragraph>\n<Task>\nSuggest improvements for this resume...",
  "provider": "mock",
  "model": "mock-model"
}
```

---

### 2.7 列出简历摘要历史

**请求**
```http
GET /api/v1/resumes/1/summary/history/
Authorization: Bearer <access_token>
```

**响应（200）**: 返回 `ResumeOptimization` 对象数组（见 2.5 格式）

---

## 3. 岗位

### 3.1 列出岗位

**请求**
```http
GET /api/v1/jobs/
```

**响应（200）**
```json
[
  {
    "id": 1,
    "title": "后端开发实习生",
    "company": "字节跳动",
    "location": "北京",
    "description": "负责抖音后端服务开发...",
    "requirements": "熟悉 Python、MySQL、Redis",
    "salary": "300-400/天",
    "work_type": "实习",
    "experience": "在校生",
    "education": "本科",
    "welfare": "免费三餐、租房补贴",
    "tags": "Python,FastAPI,MySQL",
    "source": "manual",
    "source_url": null,
    "source_id": null,
    "is_active": true,
    "publish_date": "2026-01-10T00:00:00",
    "deadline": "2026-06-30T00:00:00",
    "created_at": "2026-01-10T10:00:00",
    "updated_at": "2026-01-10T10:00:00"
  }
]
```

---

### 3.2 创建岗位

**请求**
```http
POST /api/v1/jobs/
Content-Type: application/json

{
  "title": "前端开发实习生",
  "company": "腾讯",
  "location": "深圳",
  "description": "参与微信小程序前端开发",
  "requirements": "熟悉 React、TypeScript",
  "salary": "250-350/天",
  "work_type": "实习",
  "experience": "在校生",
  "education": "本科",
  "source": "manual"
}
```

**响应（200）**: 返回创建的岗位对象

---

### 3.3 匹配岗位与简历（预览）

**请求**
```http
POST /api/v1/jobs/1/match/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "resume_id": 1
}
```

**响应（200）**
```json
{
  "mode": "job_match",
  "job_id": 1,
  "resume_id": 1,
  "score": 75,
  "feedback": "简历与岗位的匹配度较高。主要优势：熟练掌握 Python 与 FastAPI...\n建议：可加强对分布式系统的理解...",
  "raw_content": "mock-generate: Score: 75\nFeedback: 简历与岗位的匹配度较高...",
  "provider": "mock",
  "model": "mock-model"
}
```

---

### 3.4 保存岗位匹配结果（持久化）

**请求**
```http
POST /api/v1/jobs/1/match/persist/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "resume_id": 1
}
```

**响应（200）**
```json
{
  "id": 1,
  "job_id": 1,
  "resume_id": 1,
  "mode": "job_match",
  "score": 75,
  "feedback": "简历与岗位的匹配度较高。主要优势：熟练掌握 Python 与 FastAPI...",
  "raw_content": "mock-generate: Score: 75...",
  "provider": "mock",
  "model": "mock-model",
  "created_at": "2026-04-01T12:10:00",
  "updated_at": "2026-04-01T12:10:00"
}
```

---

## 4. 面试

### 4.1 生成面试题目（预览）

**请求**
```http
POST /api/v1/interview/questions/generate/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "job_context": "后端工程师实习岗位，关注 FastAPI、异步接口与清晰架构。",
  "resume_id": 1,
  "count": 3
}
```

**响应（200）**
```json
{
  "mode": "question_generation",
  "job_context": "后端工程师实习岗位，关注 FastAPI、异步接口与清晰架构。",
  "resume_context": "张三，后端开发实习生，熟悉 Python、FastAPI...",
  "count": 3,
  "questions": [
    {
      "question_number": 1,
      "question_text": "请描述 FastAPI 中依赖注入的工作原理，以及它如何提升代码的可测试性？",
      "question_type": "technical",
      "difficulty": "medium",
      "category": "FastAPI"
    },
    {
      "question_number": 2,
      "question_text": "在 Python 异步编程中，asyncio.gather 与 asyncio.wait 的区别是什么？",
      "question_type": "technical",
      "difficulty": "medium",
      "category": "Python异步"
    },
    {
      "question_number": 3,
      "question_text": "如何设计一个高可用的分布式任务队列？请从系统架构角度说明。",
      "question_type": "system_design",
      "difficulty": "hard",
      "category": "系统设计"
    }
  ],
  "raw_content": "mock-generate: <interview questions>\n<Task>\nGenerate 3 interview questions...",
  "provider": "mock",
  "model": "mock-model"
}
```

---

### 4.2 评估回答（预览）

**请求**
```http
POST /api/v1/interview/answers/evaluate/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "question_text": "请描述 FastAPI 中依赖注入的工作原理",
  "user_answer": "FastAPI 的依赖注入通过 Depends 函数实现，可以将一个可调用对象作为路径操作函数的参数默认值。",
  "job_context": "后端工程师实习岗位"
}
```

**响应（200）**
```json
{
  "mode": "answer_evaluation",
  "question_text": "请描述 FastAPI 中依赖注入的工作原理",
  "user_answer": "FastAPI 的依赖注入通过 Depends 函数实现...",
  "job_context": "后端工程师实习岗位",
  "score": 75,
  "feedback": "回答基本准确。提到了 Depends 函数的核心作用。建议进一步说明如何利用依赖注入实现数据库连接池复用和认证逻辑解耦。",
  "raw_content": "mock-generate: Score: 75..."
}
```

---

### 4.3 创建面试记录

**请求**
```http
POST /api/v1/interview/records/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "job_id": null,
  "question_id": 1,
  "user_answer": "FastAPI 的依赖注入通过 Depends 函数实现..."
}
```

**响应（200）**
```json
{
  "id": 1,
  "user_id": 1,
  "job_id": null,
  "question_id": 1,
  "user_answer": "FastAPI 的依赖注入通过 Depends 函数实现...",
  "ai_evaluation": null,
  "score": null,
  "feedback": null,
  "provider": null,
  "model": null,
  "created_at": "2026-04-01T12:15:00",
  "updated_at": "2026-04-01T12:15:00"
}
```

---

### 4.4 评估并保存面试记录

**请求**
```http
POST /api/v1/interview/records/1/evaluate/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "job_context": "后端工程师实习岗位"
}
```

**响应（200）**
```json
{
  "mode": "answer_evaluation",
  "record_id": 1,
  "score": 75,
  "feedback": "回答基本准确。提到了 Depends 函数的核心作用...",
  "ai_evaluation": "技术理解：75分。概念清晰，能正确说明 Depends 的基本用法。建议进一步完善对依赖注入生命周期的理解。",
  "raw_content": "mock-generate: Score: 75...",
  "provider": "mock",
  "model": "mock-model",
  "answered_at": "2026-04-01T12:15:00"
}
```

---

### 4.5 列出面试会话

**请求**
```http
GET /api/v1/interview/sessions/
Authorization: Bearer <access_token>
```

**响应（200）**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "job_id": null,
    "session_type": "technical",
    "duration": null,
    "total_questions": 5,
    "average_score": null,
    "completed": null,
    "created_at": "2026-04-01T12:00:00",
    "updated_at": "2026-04-01T12:00:00"
  }
]
```

---

## 5. 投递追踪

### 5.1 创建投递记录

**请求**
```http
POST /api/v1/tracker/applications/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "job_id": 1,
  "resume_id": 1,
  "status": "applied",
  "notes": "1月15日投递，等待回复"
}
```

**响应（200）**
```json
{
  "id": 1,
  "user_id": 1,
  "job_id": 1,
  "resume_id": 1,
  "status": "applied",
  "notes": "1月15日投递，等待回复",
  "application_date": "2026-04-01T00:00:00",
  "status_updated_at": "2026-04-01T12:20:00",
  "created_at": "2026-04-01T12:20:00",
  "updated_at": "2026-04-01T12:20:00"
}
```

---

### 5.2 生成投递建议（预览）

**请求**
```http
POST /api/v1/tracker/applications/1/advice/
Authorization: Bearer <access_token>
```

**响应（200）**
```json
{
  "mode": "tracker_advice",
  "application_id": 1,
  "summary": "该投递处于'已投递'阶段。建议主动跟进面试进度，同时准备该岗位的二轮面试内容。",
  "next_steps": [
    "在 3-5 个工作日后发送跟进邮件",
    "复习 FastAPI 依赖注入与异步编程相关知识点",
    "准备系统设计相关的项目经历描述"
  ],
  "risks": [
    "招聘方流程较慢，可能需要等待 2 周以上",
    "竞争激烈，建议同步投递其他公司类似岗位"
  ],
  "raw_content": "mock-generate: <one concise paragraph>...",
  "provider": "mock",
  "model": "mock-model"
}
```

---

### 5.3 保存投递建议（持久化）

**请求**
```http
POST /api/v1/tracker/applications/1/advice/persist/
Authorization: Bearer <access_token>
```

**响应（200）**
```json
{
  "id": 1,
  "application_id": 1,
  "mode": "tracker_advice",
  "summary": "该投递处于'已投递'阶段。建议主动跟进面试进度...",
  "next_steps": ["在 3-5 个工作日后发送跟进邮件", "复习 FastAPI 依赖注入与异步编程相关知识点"],
  "risks": ["招聘方流程较慢，可能需要等待 2 周以上"],
  "raw_content": "mock-generate: <one concise paragraph>...",
  "provider": "mock",
  "model": "mock-model",
  "created_at": "2026-04-01T12:25:00",
  "updated_at": "2026-04-01T12:25:00"
}
```

---

### 5.4 列出投递记录

**请求**
```http
GET /api/v1/tracker/applications/
Authorization: Bearer <access_token>
```

**响应（200）**: 返回 `ApplicationTracker` 对象数组（见 5.1 格式）

---

## 6. 健康检查

### 6.1 健康检查

**请求**
```http
GET /health
```

**响应（200）**
```json
{
  "status": "healthy"
}
```

---

### 6.2 就绪检查（含数据库）

**请求**
```http
GET /ready
```

**响应（200）**
```json
{
  "status": "ready"
}
```

**错误响应（503）**
```json
{
  "detail": "service not ready: database connection failed"
}
```

---

## 错误响应格式

所有 API 错误遵循统一格式：

| HTTP 状态码 | 含义 | 响应示例 |
|---|---|---|
| 400 | 请求参数错误 | `{"detail": "resume text is empty"}` |
| 401 | 未认证 / 令牌无效 | `{"detail": "Invalid credentials"}` |
| 403 | 无权限访问 | `{"detail": "Not authorized to access this resource"}` |
| 404 | 资源不存在 | `{"detail": "Resume not found"}` |
| 410 | 资源已废弃 | `{"detail": "Job applications are managed by /api/v1/tracker/applications/"}` |
| 429 | 请求过于频繁 | `{"detail": "Rate limit exceeded"}` |
| 500 | 服务器内部错误 | `{"detail": "Resume summary failed"}` |

---

## 认证流程总结

```
1. 登录 POST /api/v1/auth/login
   → 获得 access_token + refresh_token

2. 后续请求 Header 携带
   Authorization: Bearer <access_token>

3. access_token 过期（401）时
   → POST /api/v1/auth/refresh 用 refresh_token 换新令牌

4. 登出 POST /api/v1/auth/logout
   → 服务端撤销 refresh_token
```

---

## 7. Rate Limiting

所有 API 端点默认受 Rate Limiting 保护，防止过于频繁的请求。

### 7.1 限制参数

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `RATE_LIMIT_REQUESTS` | `100` | 单个时间窗口内允许的最大请求数 |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | 时间窗口长度（秒） |

### 7.2 限制策略

- **滑动窗口（Sliding Window）**：统计时间窗口内的请求数，精确控制突发流量
- **后端**：生产环境优先使用 Redis；本地 / 无 Redis 时自动降级为内存滑动窗口
- **Key 策略**：基于客户端 IP 地址（`X-Forwarded-For` 头内的真实 IP）

### 7.3 豁免端点

以下端点不受 Rate Limiting 限制，可自由访问：

- `GET /health`
- `GET /ready`
- `GET /metrics`

### 7.4 触发限流

**响应（429 Too Many Requests）**

```json
{
  "detail": "Rate limit exceeded. Try again later."
}
```

### 7.5 配置方式

通过环境变量配置 Rate Limiting 行为：

```bash
# 调整每分钟请求数（默认 100）
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60

# Redis 后端（生产推荐，需先启动 Redis）
REDIS_URL=redis://localhost:6379/0
```

> **本地开发默认**：使用内存滑动窗口，无需额外启动 Redis。
> **Docker Compose 部署**：默认连接 `redis` 服务，使用 Redis 滑动窗口后端。
