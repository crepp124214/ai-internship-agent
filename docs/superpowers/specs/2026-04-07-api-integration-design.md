# API 集成 + Playwright 测试 设计文档

> 版本: v1.0.0 | 状态: 设计完成 | 日期: 2026-04-07

---

## 一、目标

1. **前后端联调**：确保全部 API 端点正常通信
2. **Playwright 测试**：按功能模块覆盖核心用户路径
3. **Docker 环境**：使用 docker-compose 本地测试

---

## 二、测试范围

### Resume 模块
- POST /api/v1/resumes - 创建简历
- GET /api/v1/resumes/{id} - 获取简历
- PUT /api/v1/resumes/{id} - 更新简历
- POST /api/v1/import/resume - 简历导入（PDF/DOCX）

### Job 模块
- POST /api/v1/jobs - 创建 JD
- GET /api/v1/jobs/{id} - 获取 JD
- GET /api/v1/jobs - 搜索 JD
- POST /api/v1/import/jds - JD 批量导入（CSV/Excel）

### Interview 模块
- POST /api/v1/interview/coach/start - 启动面试
- POST /api/v1/interview/coach/answer - 提交答案
- POST /api/v1/interview/coach/end - 结束面试
- GET /api/v1/interview/coach/report/{session_id} - 获取复盘报告

### Agent 模块
- POST /api/v1/agent/chat - Agent 对话（SSE）

---

## 三、测试环境

- **Docker Compose**：前端 + 后端 + PostgreSQL + Redis
- **Playwright MCP**：浏览器自动化测试
- **测试顺序**：按模块依赖顺序执行

---

## 四、文件结构

```
tests/e2e/
  test_api_smoke.py          # 冒烟测试
  test_resume_api.py         # Resume API 测试
  test_job_api.py            # Job API 测试
  test_interview_api.py      # Interview API 测试
  test_agent_api.py          # Agent API 测试
  conftest.py                # Pytest 配置
```

---

## 五、验收标准

1. Docker Compose 环境可正常启动
2. Playwright 可连接前端页面
3. 各模块 API 测试全部通过
4. SSE 流式响应正确接收
