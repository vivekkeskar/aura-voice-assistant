from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession


class BaseTool(ABC):
    name: str
    description: str
    parameters: Dict[str, Any]

    @abstractmethod
    async def execute(self, params: Dict[str, Any], session: Optional[AsyncSession] = None) -> Dict[str, Any]:
        """Execute the tool with given parameters and return structured result."""
        pass

    def to_gemini_schema(self) -> Dict[str, Any]:
        """Convert tool definition to Gemini function declaration format."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def get_all_tools(self) -> List[BaseTool]:
        return list(self._tools.values())

    def get_gemini_declarations(self) -> List[Dict[str, Any]]:
        return [tool.to_gemini_schema() for tool in self._tools.values()]

    async def execute_tool(
        self, name: str, params: Dict[str, Any], session: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        tool = self.get_tool(name)
        if not tool:
            return {"error": f"Tool '{name}' is not registered."}
        try:
            return await tool.execute(params, session)
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}


tool_registry = ToolRegistry()
