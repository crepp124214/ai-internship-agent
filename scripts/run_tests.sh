#!/bin/bash
# 测试运行脚本

echo "======================================"
echo "AI实习求职Agent系统 - 测试运行脚本"
echo "======================================"

# 设置颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 设置测试环境变量
export APP_ENV=development

# 检查参数
TEST_TYPE=${1:-"all"}

echo ""
echo "测试类型: $TEST_TYPE"
echo ""

case $TEST_TYPE in
    "unit")
        echo -e "${YELLOW}运行单元测试...${NC}"
        pytest tests/unit/ -v --cov=src --cov-report=term --cov-report=html:htmlcov --cov-fail-under=80
        ;;
    "integration")
        echo -e "${YELLOW}运行集成测试...${NC}"
        pytest tests/integration/ -v --cov=src --cov-report=term --cov-report=html:htmlcov
        ;;
    "e2e")
        echo -e "${YELLOW}运行端到端测试...${NC}"
        APP_ENV=development pytest tests/e2e/ -v -s --cov=src --cov-report=term --cov-report=html:htmlcov
        ;;
    "all")
        echo -e "${YELLOW}运行所有测试...${NC}"
        pytest tests/ -v --cov=src --cov-report=term --cov-report=html:htmlcov --cov-fail-under=80
        ;;
    "coverage")
        echo -e "${YELLOW}生成测试覆盖率报告...${NC}"
        pytest tests/ --cov=src --cov-report=html:htmlcov --cov-report=xml:coverage.xml
        echo -e "${GREEN}覆盖率报告已生成: htmlcov/index.html${NC}"
        ;;
    "clean")
        echo -e "${YELLOW}清理测试缓存和覆盖率报告...${NC}"
        rm -rf .pytest_cache/
        rm -rf htmlcov/
        rm -f coverage.xml
        rm -f .coverage
        echo -e "${GREEN}清理完成${NC}"
        ;;
    *)
        echo -e "${RED}未知的测试类型: $TEST_TYPE${NC}"
        echo ""
        echo "用法: $0 [unit|integration|e2e|all|coverage|clean]"
        echo ""
        echo "说明:"
        echo "  unit         - 仅运行单元测试"
        echo "  integration  - 仅运行集成测试"
        echo "  e2e          - 仅运行端到端测试"
        echo "  all          - 运行所有测试（默认）"
        echo "  coverage     - 生成覆盖率报告"
        echo "  clean        - 清理测试缓存和覆盖率报告"
        exit 1
        ;;
esac

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}"
    echo "======================================"
    echo "测试通过！"
    echo "======================================"
    echo -e "${NC}"
else
    echo -e "${RED}"
    echo "======================================"
    echo "测试失败！"
    echo "======================================"
    echo -e "${NC}"
    exit $EXIT_CODE
fi
