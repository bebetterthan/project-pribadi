from typing import Dict, Type
from app.tools.base import BaseTool
from app.tools.nmap_tool import NmapTool
from app.tools.nuclei_tool import NucleiTool
from app.tools.whatweb_tool import WhatWebTool
from app.tools.sslscan_tool import SSLScanTool
from app.tools.mock_tools import MockNmapTool, MockNucleiTool, MockWhatwebTool, MockSSLScanTool
from app.utils.logger import logger


class ToolFactory:
    """Factory for creating tool instances"""

    _tools: Dict[str, Type[BaseTool]] = {
        'nmap': NmapTool,
        'nuclei': NucleiTool,
        'whatweb': WhatWebTool,
        'sslscan': SSLScanTool
    }

    _mock_tools: Dict[str, Type[BaseTool]] = {
        'nmap': MockNmapTool,
        'nuclei': MockNucleiTool,
        'whatweb': MockWhatwebTool,
        'sslscan': MockSSLScanTool
    }

    @classmethod
    def get_tool(cls, tool_name: str, use_mock: bool = False) -> BaseTool:
        """
        Get tool instance by name

        Args:
            tool_name: Name of the tool
            use_mock: If True, use mock tool. If False, try real tool first, fallback to mock
        """
        if tool_name not in cls._tools:
            raise ValueError(f"Unknown tool: {tool_name}")

        # If mock explicitly requested
        if use_mock:
            logger.info(f"Using mock tool for {tool_name}")
            return cls._mock_tools[tool_name]()

        # Try real tool first
        tool_instance = cls._tools[tool_name]()

        # Check if tool is installed
        if not tool_instance.is_installed():
            logger.warning(f"{tool_name} not installed, using mock tool instead")
            return cls._mock_tools[tool_name]()

        return tool_instance

    @classmethod
    def get_available_tools(cls) -> list:
        """Get list of available tool names"""
        return list(cls._tools.keys())
