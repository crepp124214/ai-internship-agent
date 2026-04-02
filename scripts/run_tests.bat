@echo off
REM 测试运行脚本 (Windows)

echo ======================================
echo AI实习求职Agent系统 - 测试运行脚本
echo ======================================
echo.

if "%~1"=="" set TEST_TYPE=all
set TEST_TYPE=%~1

echo 测试类型: %TEST_TYPE%
echo.

if "%TEST_TYPE%"=="unit" (
    echo 运行单元测试...
    pytest tests/unit/ -v --cov=src --cov-report=term --cov-report=html:htmlcov --cov-fail-under=80
    goto :end
)

if "%TEST_TYPE%"=="integration" (
    echo 运行集成测试...
    pytest tests/integration/ -v --cov=src --cov-report=term --cov-report=html:htmlcov
    goto :end
)

if "%TEST_TYPE%"=="e2e" (
    echo 运行端到端测试...
    pytest tests/e2e/ -v -s --cov=src --cov-report=term --cov-report=html:htmlcov
    goto :end
)

if "%TEST_TYPE%"=="all" (
    echo 运行所有测试...
    pytest tests/ -v --cov=src --cov-report=term --cov-report=html:htmlcov --cov-fail-under=80
    goto :end
)

if "%TEST_TYPE%"=="coverage" (
    echo 生成测试覆盖率报告...
    pytest tests/ --cov=src --cov-report=html:htmlcov --cov-report=xml:coverage.xml
    echo 覆盖率报告已生成: htmlcov/index.html
    goto :end
)

if "%TEST_TYPE%"=="clean" (
    echo 清理测试缓存和覆盖率报告...
    if exist .pytest_cache rmdir /s /q .pytest_cache
    if exist htmlcov rmdir /s /q htmlcov
    if exist coverage.xml del coverage.xml
    if exist .coverage del .coverage
    echo 清理完成
    goto :end
)

echo 未知的测试类型: %TEST_TYPE%
echo.
echo 用法: %~nx0 [unit^|integration^|e2e^|all^|coverage^|clean]
echo.
echo 说明:
echo   unit         - 仅运行单元测试
echo   integration  - 仅运行集成测试
echo   e2e          - 仅运行端到端测试
echo   all          - 运行所有测试（默认）
echo   coverage     - 生成覆盖率报告
echo   clean        - 清理测试缓存和覆盖率报告
exit /b 1

:end
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ======================================
    echo 测试通过！
    echo ======================================
) else (
    echo.
    echo ======================================
    echo 测试失败！
    echo ======================================
    exit /b %ERRORLEVEL%
)
