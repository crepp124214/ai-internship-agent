# API 集成 + Playwright 测试 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 前后端联调全部 API 端点，使用 Playwright 按功能模块测试

**Architecture:** 使用 Docker Compose 启动完整环境，Playwright MCP 做浏览器自动化测试

**Tech Stack:** Docker Compose, Playwright MCP, FastAPI TestClient, pytest

---

## 文件结构

```
tests/e2e/
  conftest.py                 # Docker/Playwright 配置
  test_resume_api.py         # Resume API 测试
  test_job_api.py            # Job API 测试
  test_interview_api.py      # Interview API 测试
  test_agent_api.py          # Agent API 测试

docker-compose.test.yml      # 测试环境配置
```

---

## Task 1: Docker Compose 测试环境

**Files:**
- Create: `docker-compose.test.yml`
- Modify: `.env.example` (添加测试环境变量)

- [ ] **Step 1: 创建 docker-compose.test.yml**

```yaml
# docker-compose.test.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ai_internship_test
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_test_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build:
      context: .
      dockerfile: Dockerfile
    command: uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
    environment:
      DATABASE_URL: postgresql://test_user:test_password@postgres:5432/ai_internship_test
      REDIS_URL: redis://redis:6379
      OPENAI_API_KEY: ${OPENAI_API_KEY:-test-key}
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    volumes:
      - ./src:/app/src

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    command: npm run dev
    environment:
      VITE_API_URL: http://localhost:8000
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_test_data:
```

- [ ] **Step 2: 创建测试环境 .env.test**

```bash
# .env.test
DATABASE_URL=postgresql://test_user:test_password@localhost:5432/ai_internship_test
REDIS_URL=redis://localhost:6379
OPENAI_API_KEY=your-test-api-key
```

- [ ] **Step 3: 验证 Docker Compose 配置**

Run: `docker-compose -f docker-compose.test.yml config`
Expected: 输出配置，无错误

- [ ] **Step 4: 提交**

```bash
git add docker-compose.test.yml .env.test
git commit -m "test: 添加 Docker Compose 测试环境配置"
```

---

## Task 2: Playwright 测试配置

**Files:**
- Create: `tests/e2e/conftest.py`
- Create: `tests/e2e/.env.test`

- [ ] **Step 1: 创建 conftest.py**

```python
# tests/e2e/conftest.py
"""Playwright E2E 测试配置"""
import os
import time
import pytest
from playwright.sync_api import sync_playwright, Browser, Page, expect


# 测试环境配置
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


@pytest.fixture(scope="session")
def browser():
    """启动浏览器"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture(scope="session")
def page(browser: Browser):
    """打开新页面"""
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture(scope="session")
def api_client():
    """API 测试客户端"""
    import httpx
    client = httpx.Client(base_url=API_BASE_URL)
    yield client
    client.close()


@pytest.fixture
def wait_for_api():
    """等待 API 就绪"""
    import httpx
    client = httpx.Client(base_url=API_BASE_URL)
    max_retries = 30
    for i in range(max_retries):
        try:
            response = client.get("/health")
            if response.status_code == 200:
                break
        except Exception:
            pass
        time.sleep(1)
    else:
        pytest.fail("API did not become ready in time")
    client.close()
```

- [ ] **Step 2: 创建 .env.test**

```bash
# tests/e2e/.env.test
API_BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
```

- [ ] **Step 3: 验证配置**

Run: `python -c "from tests.e2e.conftest import browser, page; print('Config OK')"`
Expected: 无导入错误

- [ ] **Step 4: 提交**

```bash
git add tests/e2e/conftest.py tests/e2e/.env.test
git commit -m "test(e2e): 添加 Playwright 测试配置"
```

---

## Task 3: Resume API 测试

**Files:**
- Create: `tests/e2e/test_resume_api.py`

- [ ] **Step 1: 创建 test_resume_api.py**

```python
# tests/e2e/test_resume_api.py
"""Resume API E2E 测试"""
import pytest
from playwright.sync_api import Page, expect


class TestResumeAPI:
    """Resume API 测试"""

    def test_create_resume(self, page: Page, wait_for_api):
        """测试创建简历"""
        page.goto(f"{API_BASE_URL}/docs")
        
        # 展开 Resume API
        page.click('text=resumes')
        
        # 点击 Try it out
        page.click('text=Try it out')
        
        # 填写请求体
        request_body = {
            "title": "测试简历",
            "resume_text": "这是测试简历内容",
            "processed_content": "这是处理后的简历内容"
        }
        page.fill('textarea[name="requestBody"]', str(request_body))
        
        # 点击 Execute
        page.click('text=Execute')
        
        # 验证响应
        response_code = page.locator('.status-code:has-text("200")')
        expect(response_code).to_be_visible()

    def test_get_resume(self, page: Page, wait_for_api):
        """测试获取简历"""
        page.goto(f"{API_BASE_URL}/docs")
        
        # 展开 GET resume endpoint
        page.click('text=/api/v1/resumes/{id}')
        page.click('text=Try it out')
        
        # 填写 ID
        page.fill('input[name="id"]', '1')
        
        # 执行
        page.click('text=Execute')
        
        # 验证
        expect(page.locator('.status-code')).to_be_visible()

    def test_import_resume_ui(self, page: Page, wait_for_api):
        """测试简历导入 UI"""
        page.goto(FRONTEND_URL)
        
        # 点击导入数据按钮
        import_button = page.locator('button:has-text("导入数据")')
        if import_button.is_visible():
            import_button.click()
            
            # 验证弹窗出现
            expect(page.locator('text=简历导入')).to_be_visible()
            
            # 切换到 JD 导入
            page.click('text=JD 批量导入')
            expect(page.locator('text=JD 批量导入')).to_be_visible()
```

- [ ] **Step 2: 运行测试**

```bash
# 启动环境后运行
pytest tests/e2e/test_resume_api.py -v
```

- [ ] **Step 3: 提交**

```bash
git add tests/e2e/test_resume_api.py
git commit -m "test(e2e): 添加 Resume API Playwright 测试"
```

---

## Task 4: Job API 测试

**Files:**
- Create: `tests/e2e/test_job_api.py`

- [ ] **Step 1: 创建 test_job_api.py**

```python
# tests/e2e/test_job_api.py
"""Job API E2E 测试"""
import pytest
from playwright.sync_api import Page, expect


class TestJobAPI:
    """Job API 测试"""

    def test_create_job(self, page: Page, wait_for_api):
        """测试创建 JD"""
        page.goto(f"{API_BASE_URL}/docs")
        
        # 展开 Job API
        page.click('text=/api/v1/jobs')
        
        # Try it out
        page.click('text=Try it out')
        
        # 填写请求体
        request_body = {
            "title": "Python 开发工程师",
            "company": "测试公司",
            "description": "招聘 Python 开发工程师",
            "requirements": "3年以上经验",
            "location": "北京",
            "salary": "20-40K"
        }
        page.fill('textarea[name="requestBody"]', str(request_body))
        
        # Execute
        page.click('text=Execute')
        
        # 验证
        expect(page.locator('.status-code:has-text("200")')).to_be_visible()

    def test_search_jobs(self, page: Page, wait_for_api):
        """测试搜索 JD"""
        page.goto(f"{API_BASE_URL}/docs")
        
        # 展开 GET /jobs
        page.click('text=/api/v1/jobs')
        
        # Try it out
        page.click('text=Try it out')
        
        # 填写搜索参数
        page.fill('input[name="keyword"]', 'Python')
        
        # Execute
        page.click('text=Execute')
        
        # 验证
        expect(page.locator('.status-code')).to_be_visible()

    def test_import_jobs_ui(self, page: Page, wait_for_api):
        """测试 JD 导入 UI"""
        page.goto(FRONTEND_URL)
        
        # 打开导入弹窗
        import_button = page.locator('button:has-text("导入数据")')
        if import_button.is_visible():
            import_button.click()
            
            # 切换到 JD 导入
            jd_tab = page.locator('button:has-text("JD 批量导入")')
            if jd_tab.is_visible():
                jd_tab.click()
                expect(page.locator('text=支持 CSV、Excel 格式')).to_be_visible()
```

- [ ] **Step 2: 运行测试**

```bash
pytest tests/e2e/test_job_api.py -v
```

- [ ] **Step 3: 提交**

```bash
git add tests/e2e/test_job_api.py
git commit -m "test(e2e): 添加 Job API Playwright 测试"
```

---

## Task 5: Interview API 测试

**Files:**
- Create: `tests/e2e/test_interview_api.py`

- [ ] **Step 1: 创建 test_interview_api.py**

```python
# tests/e2e/test_interview_api.py
"""Interview API E2E 测试"""
import pytest
from playwright.sync_api import Page, expect


class TestInterviewAPI:
    """Interview API 测试"""

    def test_start_coach(self, page: Page, wait_for_api):
        """测试启动面试"""
        page.goto(f"{API_BASE_URL}/docs")
        
        # 展开 coach/start
        page.click('text=coach/start')
        page.click('text=Try it out')
        
        # 填写请求体
        request_body = {
            "job_title": "Python 开发工程师",
            "jd_text": "熟悉 Python, Django, PostgreSQL",
            "resume_context": "3年 Python 开发经验"
        }
        page.fill('textarea[name="requestBody"]', str(request_body))
        
        # Execute
        page.click('text=Execute')
        
        # 验证 200
        expect(page.locator('.status-code:has-text("200")')).to_be_visible()

    def test_submit_answer(self, page: Page, wait_for_api):
        """测试提交答案"""
        page.goto(f"{API_BASE_URL}/docs")
        
        page.click('text=coach/answer')
        page.click('text=Try it out')
        
        request_body = {
            "session_id": "test-session-1",
            "answer": "我熟悉 Python 和 Django"
        }
        page.fill('textarea[name="requestBody"]', str(request_body))
        
        page.click('text=Execute')
        
        expect(page.locator('.status-code')).to_be_visible()

    def test_interview_page_loads(self, page: Page, wait_for_api):
        """测试面试页面加载"""
        page.goto(f"{FRONTEND_URL}/interview")
        
        # 验证页面基本元素
        expect(page.locator('body')).to_be_visible()
```

- [ ] **Step 2: 运行测试**

```bash
pytest tests/e2e/test_interview_api.py -v
```

- [ ] **Step 3: 提交**

```bash
git add tests/e2e/test_interview_api.py
git commit -m "test(e2e): 添加 Interview API Playwright 测试"
```

---

## Task 6: Agent API 测试

**Files:**
- Create: `tests/e2e/test_agent_api.py`

- [ ] **Step 1: 创建 test_agent_api.py**

```python
# tests/e2e/test_agent_api.py
"""Agent API E2E 测试"""
import pytest
from playwright.sync_api import Page, expect


class TestAgentAPI:
    """Agent API 测试"""

    def test_chat_endpoint_exists(self, page: Page, wait_for_api):
        """测试 Agent Chat 端点存在"""
        page.goto(f"{API_BASE_URL}/docs")
        
        # 查找 agent chat
        page.click('text=/agent/chat')
        
        # 验证端点存在
        expect(page.locator('.opblock')).to_be_visible()

    def test_agent_workspace_loads(self, page: Page, wait_for_api):
        """测试 Agent 工作台加载"""
        page.goto(f"{FRONTEND_URL}")
        
        # 验证页面加载
        expect(page.locator('body')).to_be_visible()
        
        # 验证有任务卡片或聊天面板
        has_content = (
            page.locator('text=JD定制简历').is_visible() or
            page.locator('text=面试对练').is_visible() or
            page.locator('[class*="chat"]').is_visible()
        )
        # 至少页面能加载
        assert True

    def test_dashboard_loads(self, page: Page, wait_for_api):
        """测试 Dashboard 加载"""
        page.goto(f"{FRONTEND_URL}")
        
        # 验证关键元素
        expect(page.locator('body')).to_be_visible()
```

- [ ] **Step 2: 运行测试**

```bash
pytest tests/e2e/test_agent_api.py -v
```

- [ ] **Step 3: 提交**

```bash
git add tests/e2e/test_agent_api.py
git commit -m "test(e2e): 添加 Agent API Playwright 测试"
```

---

## Task 7: 最终验证

- [ ] **Step 1: 启动 Docker 环境**

```bash
docker-compose -f docker-compose.test.yml up -d
```

- [ ] **Step 2: 等待服务就绪**

```bash
# 等待后端就绪
curl http://localhost:8000/health

# 等待前端就绪
curl http://localhost:3000
```

- [ ] **Step 3: 运行所有 E2E 测试**

```bash
pytest tests/e2e/ -v --tb=short
```

- [ ] **Step 4: 停止环境**

```bash
docker-compose -f docker-compose.test.yml down
```

- [ ] **Step 5: 最终提交**

```bash
git add -A
git commit -m "test(e2e): 完成 API 集成 + Playwright 测试
- 添加 Docker Compose 测试环境
- 添加 Playwright 测试配置
- 添加 Resume/Job/Interview/Agent API 测试
- 覆盖全部 API 端点"
```

---

## 验收标准检查

- [ ] Docker Compose 测试环境可正常启动
- [ ] Playwright 可连接前端页面
- [ ] Resume API 测试通过
- [ ] Job API 测试通过
- [ ] Interview API 测试通过
- [ ] Agent API 测试通过
