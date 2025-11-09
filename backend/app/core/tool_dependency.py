"""
Tool Dependency System - Phase 1, Day 2
Defines which tools depend on which other tools and enforces execution order
"""
from typing import Dict, List, Set, Optional
from enum import Enum
from app.models.scan_context import FindingType
from app.utils.logger import logger


class ToolName(str, Enum):
    """Available security tools"""
    SUBFINDER = "subfinder"
    HTTPX = "httpx"
    NMAP = "nmap"
    NUCLEI = "nuclei"
    WHATWEB = "whatweb"
    FFUF = "ffuf"
    SSLSCAN = "sslscan"
    WAFW00F = "wafw00f"


class DependencyLevel(int, Enum):
    """Tool execution levels based on dependencies"""
    LEVEL_1 = 1  # No dependencies - can run immediately
    LEVEL_2 = 2  # Depends on Level 1 tools
    LEVEL_3 = 3  # Depends on Level 2 tools
    LEVEL_4 = 4  # Deep analysis - depends on Level 3


class ToolDependency:
    """
    Defines dependency requirements for a tool
    """
    def __init__(
        self,
        tool_name: ToolName,
        level: DependencyLevel,
        required_tools: List[ToolName] = None,
        required_finding_types: List[FindingType] = None,
        optional_tools: List[ToolName] = None,
        fallback_behavior: str = "skip",
        description: str = ""
    ):
        """
        Initialize tool dependency.
        
        Args:
            tool_name: Name of this tool
            level: Execution level (1-4)
            required_tools: Tools that must complete before this can run
            required_finding_types: Types of findings that must exist
            optional_tools: Tools that enhance this tool if available
            fallback_behavior: What to do if dependencies not met ('skip', 'use_target', 'wait')
            description: Human-readable description of dependencies
        """
        self.tool_name = tool_name
        self.level = level
        self.required_tools = required_tools or []
        self.required_finding_types = required_finding_types or []
        self.optional_tools = optional_tools or []
        self.fallback_behavior = fallback_behavior
        self.description = description
    
    def __repr__(self):
        return (
            f"<ToolDependency("
            f"{self.tool_name.value}, "
            f"Level {self.level.value}, "
            f"requires={[t.value for t in self.required_tools]}"
            f")>"
        )


# ==============================================================================
# TOOL DEPENDENCY REGISTRY - The Complete Dependency Graph
# ==============================================================================

TOOL_DEPENDENCIES: Dict[ToolName, ToolDependency] = {
    # LEVEL 1: No Dependencies - Start Here
    ToolName.SUBFINDER: ToolDependency(
        tool_name=ToolName.SUBFINDER,
        level=DependencyLevel.LEVEL_1,
        required_tools=[],
        required_finding_types=[],
        fallback_behavior="use_target",
        description="Discovers subdomains via passive reconnaissance. No dependencies - runs on main domain."
    ),
    
    ToolName.NMAP: ToolDependency(
        tool_name=ToolName.NMAP,
        level=DependencyLevel.LEVEL_1,
        required_tools=[],
        required_finding_types=[],
        optional_tools=[ToolName.SUBFINDER],  # Can use subdomains if available
        fallback_behavior="use_target",
        description="Port scanning. Can run on main domain or discovered subdomains if SUBFINDER completed."
    ),
    
    # LEVEL 2: Depends on Level 1
    ToolName.HTTPX: ToolDependency(
        tool_name=ToolName.HTTPX,
        level=DependencyLevel.LEVEL_2,
        required_tools=[ToolName.SUBFINDER],
        required_finding_types=[FindingType.SUBDOMAIN],
        fallback_behavior="use_target",
        description="Probes HTTP services. Requires SUBFINDER to discover subdomains to probe."
    ),
    
    # LEVEL 3: Depends on Level 2
    ToolName.WHATWEB: ToolDependency(
        tool_name=ToolName.WHATWEB,
        level=DependencyLevel.LEVEL_3,
        required_tools=[ToolName.HTTPX],
        required_finding_types=[FindingType.HTTP_SERVICE],
        fallback_behavior="use_target",
        description="Technology fingerprinting. Requires HTTPX to identify active URLs to analyze."
    ),
    
    ToolName.NUCLEI: ToolDependency(
        tool_name=ToolName.NUCLEI,
        level=DependencyLevel.LEVEL_3,
        required_tools=[ToolName.HTTPX],
        required_finding_types=[FindingType.HTTP_SERVICE],
        optional_tools=[ToolName.WHATWEB],  # Can use tech info for targeted templates
        fallback_behavior="use_target",
        description="Vulnerability scanning. Requires HTTPX for active URLs. WHATWEB enhances template selection."
    ),
    
    ToolName.FFUF: ToolDependency(
        tool_name=ToolName.FFUF,
        level=DependencyLevel.LEVEL_3,
        required_tools=[ToolName.HTTPX],
        required_finding_types=[FindingType.HTTP_SERVICE],
        fallback_behavior="skip",
        description="Directory/file fuzzing. Requires HTTPX for active URLs. Skips if no HTTP services."
    ),
    
    ToolName.SSLSCAN: ToolDependency(
        tool_name=ToolName.SSLSCAN,
        level=DependencyLevel.LEVEL_3,
        required_tools=[ToolName.HTTPX],
        required_finding_types=[FindingType.HTTP_SERVICE],
        fallback_behavior="skip",
        description="SSL/TLS analysis. Requires HTTPX to find HTTPS services."
    ),
    
    ToolName.WAFW00F: ToolDependency(
        tool_name=ToolName.WAFW00F,
        level=DependencyLevel.LEVEL_3,
        required_tools=[ToolName.HTTPX],
        required_finding_types=[FindingType.HTTP_SERVICE],
        fallback_behavior="use_target",
        description="WAF detection. Requires HTTPX for active URLs."
    ),
}


class DependencyResolver:
    """
    Resolves tool dependencies and determines execution order
    """
    
    def __init__(self):
        """Initialize dependency resolver"""
        self.dependencies = TOOL_DEPENDENCIES
        logger.info("DependencyResolver initialized with dependency graph")
    
    def get_execution_order(self, tools: List[str]) -> List[List[str]]:
        """
        Get tools organized by execution level (for parallel execution within levels).
        
        Args:
            tools: List of tool names to execute
            
        Returns:
            List of tool groups, each group can execute in parallel
            Example: [['subfinder', 'nmap'], ['httpx'], ['nuclei', 'whatweb']]
        """
        try:
            # Convert to ToolName enum
            tool_enums = []
            for tool_str in tools:
                try:
                    tool_enums.append(ToolName(tool_str.lower()))
                except ValueError:
                    logger.warning(f"Unknown tool '{tool_str}', skipping")
            
            if not tool_enums:
                logger.warning("No valid tools to order")
                return []
            
            # Group by dependency level
            levels: Dict[int, List[str]] = {}
            for tool in tool_enums:
                if tool in self.dependencies:
                    dep = self.dependencies[tool]
                    level_num = dep.level.value
                    if level_num not in levels:
                        levels[level_num] = []
                    levels[level_num].append(tool.value)
                else:
                    logger.warning(f"No dependency info for {tool.value}, assuming Level 1")
                    if 1 not in levels:
                        levels[1] = []
                    levels[1].append(tool.value)
            
            # Sort by level and return as list of lists
            ordered = [levels[level] for level in sorted(levels.keys())]
            
            logger.info(f"Execution order: {ordered}")
            return ordered
            
        except Exception as e:
            logger.error(f"Failed to determine execution order: {e}", exc_info=True)
            # Fallback: return all tools in one group
            return [tools]
    
    def check_dependencies_met(
        self,
        tool_name: str,
        scan_context_manager,
        scan_id: str
    ) -> tuple[bool, str]:
        """
        Check if all dependencies for a tool are satisfied.
        
        Args:
            tool_name: Tool to check
            scan_context_manager: ScanContextManager instance
            scan_id: Scan identifier
            
        Returns:
            (ready: bool, reason: str)
            - (True, "ready") if can proceed
            - (False, "missing: subfinder") if dependency not met
        """
        try:
            tool_enum = ToolName(tool_name.lower())
            
            if tool_enum not in self.dependencies:
                logger.warning(f"No dependency info for {tool_name}, assuming ready")
                return (True, "ready")
            
            dep = self.dependencies[tool_enum]
            
            # Check required finding types exist in scan context
            for finding_type in dep.required_finding_types:
                if not scan_context_manager.has_findings(scan_id, finding_type):
                    reason = f"missing required finding type: {finding_type.value}"
                    logger.debug(f"{tool_name} not ready: {reason}")
                    return (False, reason)
            
            # All checks passed
            logger.debug(f"{tool_name} dependencies satisfied")
            return (True, "ready")
            
        except ValueError:
            logger.warning(f"Unknown tool '{tool_name}', assuming ready")
            return (True, "ready")
        except Exception as e:
            logger.error(f"Error checking dependencies for {tool_name}: {e}", exc_info=True)
            # On error, assume ready to not block scans
            return (True, f"error checking: {str(e)}")
    
    def get_dependency_info(self, tool_name: str) -> Optional[ToolDependency]:
        """
        Get dependency information for a tool.
        
        Args:
            tool_name: Tool name
            
        Returns:
            ToolDependency object or None if not found
        """
        try:
            tool_enum = ToolName(tool_name.lower())
            return self.dependencies.get(tool_enum)
        except ValueError:
            logger.warning(f"Unknown tool '{tool_name}'")
            return None
    
    def get_required_tools(self, tool_name: str) -> List[str]:
        """
        Get list of tools that must complete before this tool can run.
        
        Args:
            tool_name: Tool name
            
        Returns:
            List of required tool names
        """
        dep = self.get_dependency_info(tool_name)
        if dep:
            return [t.value for t in dep.required_tools]
        return []
    
    def get_required_findings(self, tool_name: str) -> List[FindingType]:
        """
        Get list of finding types required for this tool.
        
        Args:
            tool_name: Tool name
            
        Returns:
            List of required FindingType enums
        """
        dep = self.get_dependency_info(tool_name)
        if dep:
            return dep.required_finding_types
        return []
    
    def should_skip_tool(
        self,
        tool_name: str,
        scan_context_manager,
        scan_id: str
    ) -> tuple[bool, str]:
        """
        Determine if a tool should be skipped based on dependencies.
        
        Args:
            tool_name: Tool to check
            scan_context_manager: ScanContextManager instance
            scan_id: Scan identifier
            
        Returns:
            (skip: bool, reason: str)
        """
        dep = self.get_dependency_info(tool_name)
        if not dep:
            return (False, "")
        
        ready, reason = self.check_dependencies_met(tool_name, scan_context_manager, scan_id)
        
        if not ready:
            # Check fallback behavior
            if dep.fallback_behavior == "skip":
                return (True, f"Skipping {tool_name}: {reason}")
            elif dep.fallback_behavior == "use_target":
                return (False, f"Using fallback target for {tool_name}: {reason}")
        
        return (False, "")
    
    def visualize_dependency_graph(self) -> str:
        """
        Generate ASCII art visualization of dependency graph.
        
        Returns:
            String with dependency graph visualization
        """
        lines = []
        lines.append("="*60)
        lines.append("TOOL DEPENDENCY GRAPH")
        lines.append("="*60)
        
        # Group by level
        by_level: Dict[int, List[ToolDependency]] = {}
        for dep in self.dependencies.values():
            level = dep.level.value
            if level not in by_level:
                by_level[level] = []
            by_level[level].append(dep)
        
        # Print each level
        for level in sorted(by_level.keys()):
            lines.append(f"\nLEVEL {level}:")
            lines.append("-" * 60)
            for dep in by_level[level]:
                lines.append(f"  {dep.tool_name.value.upper()}")
                if dep.required_tools:
                    req = ", ".join([t.value for t in dep.required_tools])
                    lines.append(f"    Requires: {req}")
                if dep.required_finding_types:
                    findings = ", ".join([f.value for f in dep.required_finding_types])
                    lines.append(f"    Needs: {findings}")
                if dep.optional_tools:
                    opt = ", ".join([t.value for t in dep.optional_tools])
                    lines.append(f"    Optional: {opt}")
                lines.append(f"    Fallback: {dep.fallback_behavior}")
                lines.append("")
        
        lines.append("="*60)
        return "\n".join(lines)

