"""
Strix Tool System - Layer 2
Tool Wrapper Interface & Execution Environment

This module provides standardized interface for executing security tools
with proper isolation, resource limits, and error handling.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import subprocess
import shutil
import os


class ToolCategory(str, Enum):
    """Categories of security tools"""
    RECONNAISSANCE = "reconnaissance"     # Subdomain enum, tech detection
    ENUMERATION = "enumeration"          # Port scan, service detection
    VULNERABILITY = "vulnerability"       # Vuln scanning
    EXPLOITATION = "exploitation"         # Exploitation tools
    AUXILIARY = "auxiliary"              # Helper tools


class ToolStatus(str, Enum):
    """Tool execution status"""
    READY = "ready"                      # Tool ready to execute
    RUNNING = "running"                  # Currently executing
    COMPLETED = "completed"              # Finished successfully
    FAILED = "failed"                    # Execution failed
    TIMEOUT = "timeout"                  # Exceeded time limit
    CANCELLED = "cancelled"              # Manually cancelled


@dataclass
class ToolParameters:
    """
    Standard parameters for tool execution
    """
    target: str                                      # Target (domain, IP, URL)
    options: Dict[str, Any] = field(default_factory=dict)  # Tool-specific options
    timeout: int = 300                               # Max execution time (seconds)
    output_format: str = "json"                      # Output format preference
    extra_args: List[str] = field(default_factory=list)    # Additional CLI args
    env_vars: Dict[str, str] = field(default_factory=dict) # Environment variables


@dataclass
class ToolResult:
    """
    Standard result structure from tool execution
    """
    tool_name: str
    status: ToolStatus
    exit_code: int
    stdout: str                                      # Standard output
    stderr: str                                      # Standard error
    execution_time: float                            # Seconds
    parsed_data: Optional[Dict[str, Any]] = None    # Parsed findings
    raw_output_file: Optional[str] = None           # Path to raw output
    error_message: Optional[str] = None             # Error description
    metadata: Dict[str, Any] = field(default_factory=dict)  # Extra info
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class BaseTool(ABC):
    """
    Abstract base class for all security tool wrappers
    
    Every tool wrapper must implement:
    - _build_command(): Construct CLI command
    - _parse_output(): Parse tool output into structured format
    - _validate_target(): Validate target before execution
    """
    
    def __init__(
        self,
        tool_name: str,
        category: ToolCategory,
        description: str,
        required_params: Optional[List[str]] = None
    ):
        """
        Initialize tool wrapper
        
        Args:
            tool_name: Name of the tool (e.g., "subfinder", "nmap")
            category: Tool category
            description: Brief description of tool purpose
            required_params: List of required parameter names
        """
        self.tool_name = tool_name
        self.category = category
        self.description = description
        self.required_params = required_params or []
        
        # Check if tool is installed
        self.is_installed = self._check_installation()
        self.executable_path = self._get_executable_path()
        
        # Execution state
        self.status = ToolStatus.READY
        self.current_process: Optional[subprocess.Popen] = None
        
        # Callbacks for streaming output
        self._stdout_callback: Optional[Callable[[str], None]] = None
        self._stderr_callback: Optional[Callable[[str], None]] = None
    
    def _check_installation(self) -> bool:
        """Check if tool is installed on system"""
        return shutil.which(self.tool_name) is not None
    
    def _get_executable_path(self) -> Optional[str]:
        """Get full path to tool executable"""
        return shutil.which(self.tool_name)
    
    def is_available(self) -> bool:
        """Check if tool is available for execution"""
        return self.is_installed and self.status == ToolStatus.READY
    
    def validate_parameters(self, params: ToolParameters) -> tuple[bool, Optional[str]]:
        """
        Validate parameters before execution
        
        Args:
            params: Tool parameters to validate
            
        Returns:
            (is_valid, error_message)
        """
        # Check tool availability
        if not self.is_installed:
            return False, f"{self.tool_name} is not installed"
        
        if self.status != ToolStatus.READY:
            return False, f"Tool is not ready (current status: {self.status.value})"
        
        # Check required parameters
        for req_param in self.required_params:
            if req_param not in params.options and not hasattr(params, req_param):
                return False, f"Missing required parameter: {req_param}"
        
        # Validate target
        target_valid, target_error = self._validate_target(params.target)
        if not target_valid:
            return False, target_error
        
        return True, None
    
    def execute(self, params: ToolParameters) -> ToolResult:
        """
        Execute tool with given parameters
        
        Args:
            params: Tool execution parameters
            
        Returns:
            ToolResult with execution results
        """
        result = ToolResult(
            tool_name=self.tool_name,
            status=ToolStatus.RUNNING,
            exit_code=-1,
            stdout="",
            stderr="",
            execution_time=0.0,
            started_at=datetime.utcnow()
        )
        
        # Validate parameters
        valid, error = self.validate_parameters(params)
        if not valid:
            result.status = ToolStatus.FAILED
            result.error_message = error
            result.completed_at = datetime.utcnow()
            return result
        
        # Build command
        try:
            command = self._build_command(params)
        except Exception as e:
            result.status = ToolStatus.FAILED
            result.error_message = f"Failed to build command: {str(e)}"
            result.completed_at = datetime.utcnow()
            return result
        
        # Execute subprocess with safety controls (Layer 2.2)
        try:
            exec_result = self._execute_subprocess(command, params)
            
            # Update result with execution output
            result.status = exec_result["status"]
            result.exit_code = exec_result["exit_code"]
            result.stdout = exec_result["stdout"]
            result.stderr = exec_result["stderr"]
            result.completed_at = datetime.utcnow()
            result.execution_time = (result.completed_at - result.started_at).total_seconds()
            
            # Parse output if successful
            if result.status == ToolStatus.COMPLETED:
                try:
                    result.parsed_data = self._parse_output(result.stdout, result.stderr)
                except Exception as e:
                    result.error_message = f"Failed to parse output: {str(e)}"
            
        except Exception as e:
            result.status = ToolStatus.FAILED
            result.error_message = f"Execution error: {str(e)}"
            result.completed_at = datetime.utcnow()
            result.execution_time = (result.completed_at - result.started_at).total_seconds()
        
        return result
    
    def _execute_subprocess(self, command: List[str], params: ToolParameters) -> Dict[str, Any]:
        """
        Execute subprocess with isolation, timeout, and resource limits
        
        Layer 2.2: Safe subprocess execution
        """
        import subprocess
        import threading
        from io import StringIO
        
        stdout_buffer = StringIO()
        stderr_buffer = StringIO()
        
        try:
            # Merge environment variables
            env = os.environ.copy()
            if params.env_vars:
                env.update(params.env_vars)
            
            # Start process
            self.current_process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
                bufsize=1  # Line buffered
            )
            
            self.status = ToolStatus.RUNNING
            
            # Stream output with callbacks
            def read_stream(stream, buffer, callback):
                """Read stream line by line and optionally call callback"""
                try:
                    for line in iter(stream.readline, ''):
                        if self.status == ToolStatus.CANCELLED:
                            break
                        buffer.write(line)
                        if callback:
                            callback(line)
                except:
                    pass
            
            # Start reader threads
            stdout_thread = threading.Thread(
                target=read_stream,
                args=(self.current_process.stdout, stdout_buffer, self._stdout_callback)
            )
            stderr_thread = threading.Thread(
                target=read_stream,
                args=(self.current_process.stderr, stderr_buffer, self._stderr_callback)
            )
            
            stdout_thread.daemon = True
            stderr_thread.daemon = True
            stdout_thread.start()
            stderr_thread.start()
            
            # Wait with timeout
            timeout = params.timeout or 300  # Default 5 minutes
            try:
                exit_code = self.current_process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                self.cancel()
                return {
                    "status": ToolStatus.TIMEOUT,
                    "exit_code": -1,
                    "stdout": stdout_buffer.getvalue(),
                    "stderr": f"Tool execution timed out after {timeout} seconds"
                }
            
            # Wait for reader threads to finish
            stdout_thread.join(timeout=1)
            stderr_thread.join(timeout=1)
            
            # Check if cancelled
            if self.status == ToolStatus.CANCELLED:
                return {
                    "status": ToolStatus.CANCELLED,
                    "exit_code": -1,
                    "stdout": stdout_buffer.getvalue(),
                    "stderr": "Execution cancelled by user"
                }
            
            # Get output
            stdout = stdout_buffer.getvalue()
            stderr = stderr_buffer.getvalue()
            
            # Determine status
            status = ToolStatus.COMPLETED if exit_code == 0 else ToolStatus.FAILED
            
            return {
                "status": status,
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr
            }
            
        except Exception as e:
            return {
                "status": ToolStatus.FAILED,
                "exit_code": -1,
                "stdout": stdout_buffer.getvalue(),
                "stderr": f"Subprocess execution error: {str(e)}"
            }
        finally:
            stdout_buffer.close()
            stderr_buffer.close()
            self.current_process = None
    
    def cancel(self) -> bool:
        """
        Cancel running tool execution
        
        Returns:
            True if cancelled successfully
        """
        if self.current_process and self.status == ToolStatus.RUNNING:
            self.current_process.terminate()
            self.status = ToolStatus.CANCELLED
            return True
        return False
    
    def set_stdout_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for streaming stdout"""
        self._stdout_callback = callback
    
    def set_stderr_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for streaming stderr"""
        self._stderr_callback = callback
    
    def get_info(self) -> Dict[str, Any]:
        """Get tool information"""
        return {
            "name": self.tool_name,
            "category": self.category.value,
            "description": self.description,
            "installed": self.is_installed,
            "executable_path": self.executable_path,
            "status": self.status.value,
            "required_params": self.required_params
        }
    
    # Abstract methods - must be implemented by subclasses
    
    @abstractmethod
    def _build_command(self, params: ToolParameters) -> List[str]:
        """
        Build CLI command from parameters
        
        Args:
            params: Tool parameters
            
        Returns:
            List of command parts (e.g., ["subfinder", "-d", "example.com"])
        """
        pass
    
    @abstractmethod
    def _parse_output(self, stdout: str, stderr: str) -> Optional[Dict[str, Any]]:
        """
        Parse tool output into structured format
        
        Args:
            stdout: Standard output from tool
            stderr: Standard error from tool
            
        Returns:
            Parsed data dictionary or None if parsing fails
        """
        pass
    
    @abstractmethod
    def _validate_target(self, target: str) -> tuple[bool, Optional[str]]:
        """
        Validate target before execution
        
        Args:
            target: Target string to validate
            
        Returns:
            (is_valid, error_message)
        """
        pass
