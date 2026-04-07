import pytest
from src.core.tools.base_tool import BaseTool
from src.core.runtime.tool_registry import ToolRegistry


class FakeToolInput:
    pass


class FakeTool(BaseTool):
    name: str = "fake_tool"
    description: str = "A fake tool for testing"

    def _execute_sync(self, tool_input: dict, runtime=None, context=None) -> dict:
        return {"result": f"fake result for {tool_input.get('input', '')}"}


@pytest.fixture
def registry():
    return ToolRegistry()


def test_register_adds_tool(registry):
    tool = FakeTool()
    registry.register(tool)
    assert registry.get_tool("fake_tool") is tool


def test_get_tool_not_found_raises(registry):
    with pytest.raises(ValueError, match="Tool.*not found"):
        registry.get_tool("nonexistent")


def test_list_tools_returns_schemas(registry):
    tool = FakeTool()
    registry.register(tool)
    schemas = registry.list_tools()
    assert len(schemas) == 1
    assert schemas[0]["name"] == "fake_tool"
    assert schemas[0]["description"] == "A fake tool for testing"


def test_get_schemas_for_llm(registry):
    tool = FakeTool()
    registry.register(tool)
    schemas = registry.get_schemas()
    assert len(schemas) == 1
    assert schemas[0]["type"] == "function"
    assert "fake_tool" in schemas[0]["function"]["name"]


def test_execute_tool_calls_run(registry):
    tool = FakeTool()
    registry.register(tool)
    result = registry.execute("fake_tool", {"input": "test"})
    assert result["result"] == "fake result for test"


def test_execute_unknown_tool_raises(registry):
    with pytest.raises(ValueError, match="Tool.*not found"):
        registry.execute("unknown_tool", {})