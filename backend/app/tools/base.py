from abc import ABC, abstractmethod
from typing import Dict, Any, List
from dataclasses import dataclass
import subprocess
import time


@dataclass
class ToolResult:
    tool_name: str
    exit_code: int
    stdout: str
    stderr: str
    execution_time: float
    parsed_data: Dict[str, Any] = None


class BaseTool(ABC):
    """Abstract base class for pentesting tools"""

    def __init__(self):
        self.name: str = ""
        self.timeout: int = 300  # 5 minutes default

    @abstractmethod
    def is_installed(self) -> bool:
        """Check if tool is installed and accessible"""
        pass

    @abstractmethod
    def build_command(self, target: str, profile: str) -> List[str]:
        """Build command arguments list"""
        pass

    @abstractmethod
    def parse_output(self, stdout: str) -> Dict[str, Any]:
        """Parse tool output to structured data"""
        pass

    def execute(self, target: str, profile: str = 'normal') -> ToolResult:
        """Execute tool and return result"""
        from app.core.exceptions import ToolNotInstalledError

        if not self.is_installed():
            raise ToolNotInstalledError(f"{self.name} is not installed")

        cmd = self.build_command(target, profile)

        start_time = time.time()

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                shell=False  # CRITICAL: Never use shell=True
            )

            execution_time = time.time() - start_time

            parsed = None
            if result.returncode == 0:
                try:
                    parsed = self.parse_output(result.stdout)
                except Exception as e:
                    parsed = {"parse_error": str(e)}

            return ToolResult(
                tool_name=self.name,
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                execution_time=execution_time,
                parsed_data=parsed
            )

        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return ToolResult(
                tool_name=self.name,
                exit_code=-1,
                stdout="",
                stderr=f"Timeout after {self.timeout} seconds",
                execution_time=execution_time
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return ToolResult(
                tool_name=self.name,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                execution_time=execution_time
            )
