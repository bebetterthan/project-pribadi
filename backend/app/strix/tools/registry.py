"""
Tool Registry
Central registry for all available security tools
"""
from typing import Dict, List, Optional, Type, Any
from app.strix.tools.base import BaseTool, ToolCategory
from app.utils.logger import logger


class ToolRegistry:
    """
    Registry for managing available security tools
    
    Provides:
    - Tool discovery and registration
    - Tool lookup by name or category
    - Tool availability checking
    """
    
    def __init__(self):
        self._tools: Dict[str, Type[BaseTool]] = {}
        self._instances: Dict[str, BaseTool] = {}
    
    def register(self, tool_class: Type[BaseTool]) -> None:
        """
        Register a tool class
        
        Args:
            tool_class: Tool class to register
        """
        # Get tool name from class attribute or attempt instantiation
        # Try to access class-level attributes first
        if hasattr(tool_class, 'tool_name'):
            tool_name = tool_class.tool_name  # type: ignore
            self._tools[tool_name] = tool_class
            # Don't create instance here, only when needed
            logger.info(f"[REGISTRY] Registered tool class: {tool_name}")
        else:
            # If no class attribute, log error
            logger.error(f"[REGISTRY] Cannot register tool {tool_class.__name__}: missing tool_name attribute")
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """
        Get tool instance by name (creates instance on first access)
        
        Args:
            tool_name: Name of tool
            
        Returns:
            Tool instance or None if not found
        """
        # Return cached instance if exists
        if tool_name in self._instances:
            return self._instances[tool_name]
        
        # Create new instance from registered class
        tool_class = self._tools.get(tool_name)
        if tool_class:
            # Note: Actual tool implementations should override __init__ 
            # to provide proper defaults or class-level attributes
            # This will fail for abstract BaseTool but work for concrete implementations
            try:
                instance = tool_class()  # type: ignore
                self._instances[tool_name] = instance
                return instance
            except TypeError as e:
                logger.error(f"[REGISTRY] Failed to instantiate {tool_name}: {e}")
                return None
        
        return None
    
    def get_tools_by_category(self, category: ToolCategory) -> List[BaseTool]:
        """
        Get all tools in a category
        
        Args:
            category: Tool category
            
        Returns:
            List of tool instances
        """
        return [
            tool for tool in self._instances.values()
            if tool.category == category
        ]
    
    def get_available_tools(self) -> List[BaseTool]:
        """
        Get all available (installed) tools
        
        Returns:
            List of available tool instances
        """
        return [
            tool for tool in self._instances.values()
            if tool.is_available()
        ]
    
    def list_all_tools(self) -> List[Dict[str, Any]]:
        """
        List all registered tools with their info
        
        Returns:
            List of tool info dictionaries
        """
        return [tool.get_info() for tool in self._instances.values()]
    
    def is_tool_available(self, tool_name: str) -> bool:
        """
        Check if specific tool is available
        
        Args:
            tool_name: Name of tool
            
        Returns:
            True if tool is installed and ready
        """
        tool = self.get_tool(tool_name)
        return tool.is_available() if tool else False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        total = len(self._tools)
        available = len(self.get_available_tools())
        by_category = {}
        
        for tool in self._instances.values():
            cat = tool.category.value
            by_category[cat] = by_category.get(cat, 0) + 1
        
        return {
            "total_registered": total,
            "available": available,
            "unavailable": total - available,
            "by_category": by_category
        }


# Global registry instance
_tool_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get or create global tool registry"""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
        logger.info("[REGISTRY] Tool registry initialized")
    return _tool_registry


def register_tool(tool_class: Type[BaseTool]) -> None:
    """Register a tool class in global registry"""
    registry = get_tool_registry()
    registry.register(tool_class)
