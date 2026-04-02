# 测试文档

## 测试概述

本项目采用三层测试策略，确保代码质量和系统稳定性：

1. **单元测试** (Unit Tests) - 测试单个组件和函数
2. **集成测试** (Integration Tests) - 测试组件间的交互
3. **端端测试** (E2E Tests) - 测试完整的用户流程

## 测试覆盖率目标

- **核心业务逻辑**: ≥ 90%
- **工具函数**: ≥ 80%
- **API接口**: ≥ 70%
- **整体覆盖率**: ≥ 80%

## 测试结构

```
tests/
├── conftest.py              # pytest配置和fixtures
├── unit/                    # 单元测试
│   ├── test_resume_agent.py # Agent基类测试
│   ├── test_llm_adapter.py  # LLM适配器测试
│   ├── test_resume_service.py # 简历服务测试
│   ├── test_user_service.py   # 用户服务测试
│   └── test_repositories.py   # Repository测试
├── integration/             # 集成测试
│   ├── test_api.py          # API集成测试
│   └── test_database.py     # 数据库集成测试
└── e2e/                    # 端到端测试
    └── test_user_flow.py    # 用户完整流程测试
```

## 运行测试

### 使用脚本运行（推荐）

#### Linux/Mac
```bash
# 运行所有测试
bash scripts/run_tests.sh

# 仅运行单元测试
bash scripts/run_tests.sh unit

# 仅运行集成测试
bash scripts/run_tests.sh integration

# 仅运行端到端测试
bash scripts/run_tests.sh e2e

# 生成覆盖率报告
bash scripts/run_tests.sh coverage

# 清理测试缓存
bash scripts/run_tests.sh clean
```

#### Windows
```cmd
REM 运行所有测试
scripts\run_tests.bat

REM 仅运行单元测试
scripts\run_tests.bat unit

REM 仅运行集成测试
scripts\run_tests.bat integration

REM 仅运行端到端测试
scripts\run_tests.bat e2e

REM 生成覆盖率报告
scripts\run_tests.bat coverage

REM 清理测试缓存
scripts\run_tests.bat clean
```

### 使用pytest直接运行

```bash
# 运行所有测试
pytest tests/ -v

# 运行单元测试
pytest tests/unit/ -v

# 运行集成测试
pytest tests/integration/ -v

# 运行端到端测试
pytest tests/e2e/ -v -s

# 生成覆盖率报告
pytest tests/ --cov=src --cov-report=html:htmlcov --cov-report=term

# 运行特定测试文件
pytest tests/unit/business_logic/test_user_service.py -v

# 运行特定测试类
pytest tests/unit/business_logic/test_user_service.py::TestUserService -v

# 运行特定测试方法
pytest tests/unit/business_logic/test_user_service.py::TestUserService::test_create_user -v

# 运行带有标记的测试
pytest tests/ -m unit -v
```

## 查看覆盖率报告

生成覆盖率报告后，可以在浏览器中查看：

```bash
# 生成覆盖率报告
pytest tests/ --cov=src --cov-report=html:htmlcov

# 在浏览器中打开
# Mac/Linux: open htmlcov/index.html
# Windows: start htmlcov/index.html
```

## 测试标记

测试使用pytest标记进行分类：

- `@pytest.mark.unit` - 单元测试
- `@pytest.mark.integration` - 集成测试
- `@pytest.mark.e2e` - 端到端测试
- `@pytest.mark.slow` - 慢速测试

## 测试Fixture

主要fixture定义在 `tests/conftest.py`：

- `sample_config` - 示例配置
- `sample_resume_text` - 示例简历文本
- `sample_user_data` - 示例用户数据
- `sample_resume_data` - 示例简历数据
- `test_db` - 测试数据库会话
- `llm_config` - LLM配置
- `agent_config` - Agent配置

## 编写测试指南

### 单元测试示例

```python
import pytest
from unittest.mock import patch, MagicMock

class TestUserService:
    """测试用户服务"""

    @pytest.mark.asyncio
    async def test_create_user(self):
        """测试创建用户"""
        # 准备测试数据
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="password123"
        )

        # 使用mock模拟依赖
        with patch('path.to.user_repository') as mock_repo:
            mock_repo.create.return_value = MagicMock(id=1)

            # 执行测试
            result = await user_service.create_user(db, user_data)

            # 验证结果
            assert result is not None
            assert result.id == 1
            mock_repo.create.assert_called_once()
```

### 集成测试示例

```python
from fastapi.testclient import TestClient

def test_create_user_api(client):
    """测试创建用户API"""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    }

    response = client.post("/api/v1/users/", json=user_data)

    assert response.status_code == 200
    assert response.json()["username"] == "testuser"
```

### 端到端测试示例

```python
def test_user_registration_flow(client):
    """测试用户注册流程"""
    # 注册
    user_data = {...}
    response = client.post("/api/v1/users/", json=user_data)
    user_id = response.json()["id"]

    # 获取用户信息

    get_response = client.get(f"/api/v1/users/{user_id}")
    assert get_response.status_code == 200

    # 更新用户
    update_data = {"name": "新名字"}
    update_response = client.put(f"/api/v1/users/{user_id}", json=update_data)
    assert update_response.json()["name"] == "新名字"
```

## 测试最佳实践

1. **命名规范**
   - 测试文件: `test_*.py`
   - 测试类: `Test*`
   - 测试方法: `test_*`

2. **AAA原则**
   - Arrange (准备)
   - Act (执行)
   - Assert (验证)

3. **独立性**
   - 每个测试应该独立运行
   - 不依赖其他测试的执行顺序
   - 使用fixture进行资源管理

4. **清晰性**
   - 测试名称应该描述测试内容
   - 添加docstring说明测试目的
   - 使用有意义的断言消息

5. **覆盖率**
   - 关注测试覆盖率但不过度追求数字
   - 优先测试关键业务逻辑
   - 确保边界条件和错误处理被测试

## 故障排查

### 测试失败常见原因

1. **数据库连接问题**
   - 确保测试使用内存数据库
   - 检查fixture是否正确设置

2. **异步测试问题**
   - 使用 `@pytest.mark.asyncio` 标记
   - 确保使用 `await` 调用异步函数

3. **Mock设置不正确**
   - 检查mock的返回值
   - 验证mock是否被正确调用

4. **依赖问题**
   - 确保所有依赖已安装
   - 检查版本兼容性

## 持续集成

测试应该在CI/CD流程中运行：

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      - name: Run tests
        run: |
          pytest tests/ -v --cov=src --cov-fail-under=80
```

## 更多资源

- [pytest官方文档](https://docs.pytest.org/)
- [pytest-asyncio文档](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov文档](https://pytest-cov.readthedocs.io/)
