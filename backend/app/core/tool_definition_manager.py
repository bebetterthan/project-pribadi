"""
Tool Definition Manager - Safe Tool Schema Management

PURPOSE:
    Manage tool definitions separately for Flash and Pro models
    to prevent protobuf reuse bugs.

KEY PRINCIPLE:
    NEVER reuse tool schema instances between models.
    ALWAYS generate fresh definitions per request.

ARCHITECTURE:
    Flash Request → create_security_tools() → Fresh Flash Tools
    Pro Request   → create_security_tools() → Fresh Pro Tools (separate!)
    
NO SCHEMA SHARING. NO INSTANCE REUSE. FRESH EVERY TIME.
"""
from typing import List
import google.ai.generativelanguage as glm
from app.utils.logger import logger


class ToolDefinitionManager:
    """
    Manages tool definitions with strict isolation between models
    
    This prevents protobuf schema reuse that can trigger '\n description' bugs
    """
    
    @staticmethod
    def get_flash_tools() -> List[glm.Tool]:
        """
        Get FRESH tool definitions for Flash model (reconnaissance phase)
        
        Returns:
            New list of glm.Tool objects (NEVER reused)
            
        Tools for Flash:
            - Reconnaissance tools (subfinder, nmap, httpx, whatweb)
            - Fast execution
            - Low-cost operations
        """
        from app.tools.function_toolbox import create_security_tools
        
        # Create FRESH tools (new instances every time)
        tools = create_security_tools()
        
        logger.debug(f"[Flash] Created {len(tools[0].function_declarations)} fresh tool definitions")
        
        # Validate schemas (defensive programming)
        ToolDefinitionManager._validate_tool_schemas(tools, "Flash")
        
        return tools
    
    @staticmethod
    def get_pro_tools() -> List[glm.Tool]:
        """
        Get FRESH tool definitions for Pro model (deep analysis phase)
        
        Returns:
            New list of glm.Tool objects (completely separate from Flash tools)
            
        Tools for Pro:
            - All reconnaissance tools (for additional scans if needed)
            - Analysis tools (same as Flash for now)
            - Future: Pro-specific tools (exploit research, advanced enumeration)
        """
        from app.tools.function_toolbox import create_security_tools
        
        # Create FRESH tools (NEVER reuse Flash tools!)
        tools = create_security_tools()
        
        logger.debug(f"[Pro] Created {len(tools[0].function_declarations)} fresh tool definitions")
        
        # Validate schemas
        ToolDefinitionManager._validate_tool_schemas(tools, "Pro")
        
        return tools
    
    @staticmethod
    def _validate_tool_schemas(tools: List[glm.Tool], model_name: str) -> None:
        """
        Validate tool schemas for correctness
        
        Args:
            tools: List of glm.Tool objects
            model_name: "Flash" or "Pro" (for logging)
            
        Raises:
            ValueError: If schemas are invalid
        """
        if not tools:
            raise ValueError(f"{model_name} tools list is empty")
        
        if not isinstance(tools, list):
            raise ValueError(f"{model_name} tools must be a list, got {type(tools)}")
        
        # Check first item is a glm.Tool
        if not tools or not hasattr(tools[0], 'function_declarations'):
            raise ValueError(f"{model_name} tools[0] is not a valid glm.Tool")
        
        function_declarations = tools[0].function_declarations
        
        if not function_declarations:
            raise ValueError(f"{model_name} has no function declarations")
        
        # Validate each function declaration
        for func_decl in function_declarations:
            if not hasattr(func_decl, 'name'):
                raise ValueError(f"{model_name} function declaration missing 'name'")
            
            if not hasattr(func_decl, 'description'):
                raise ValueError(f"{model_name} function '{func_decl.name}' missing 'description'")
            
            if not hasattr(func_decl, 'parameters'):
                raise ValueError(f"{model_name} function '{func_decl.name}' missing 'parameters'")
            
            # Check for problematic characters in name/description
            if '\n' in func_decl.name or '\r' in func_decl.name:
                raise ValueError(f"{model_name} function name contains newlines: {repr(func_decl.name)}")
            
            # Validate parameters schema
            if hasattr(func_decl.parameters, 'properties'):
                for prop_name in func_decl.parameters.properties:
                    # Check for malformed property names (the '\n description' bug!)
                    if '\n' in prop_name or '\r' in prop_name or '\t' in prop_name:
                        logger.warning(
                            f"[{model_name}] DETECTED MALFORMED PROPERTY: {repr(prop_name)} in {func_decl.name}. "
                            "This may trigger Gemini SDK bugs!"
                        )
        
        logger.debug(f"[{model_name}] [OK] Validated {len(function_declarations)} tool schemas")
    
    @staticmethod
    def get_tool_count() -> dict:
        """
        Get tool count for both models (diagnostic utility)
        
        Returns:
            Dict with counts: {"flash": int, "pro": int}
        """
        flash_tools = ToolDefinitionManager.get_flash_tools()
        pro_tools = ToolDefinitionManager.get_pro_tools()
        
        return {
            "flash": len(flash_tools[0].function_declarations) if flash_tools else 0,
            "pro": len(pro_tools[0].function_declarations) if pro_tools else 0
        }
    
    @staticmethod
    def get_tool_names() -> dict:
        """
        Get tool names for both models (diagnostic utility)
        
        Returns:
            Dict with tool names: {"flash": [names], "pro": [names]}
        """
        flash_tools = ToolDefinitionManager.get_flash_tools()
        pro_tools = ToolDefinitionManager.get_pro_tools()
        
        flash_names = [f.name for f in flash_tools[0].function_declarations] if flash_tools else []
        pro_names = [f.name for f in pro_tools[0].function_declarations] if pro_tools else []
        
        return {
            "flash": flash_names,
            "pro": pro_names
        }

