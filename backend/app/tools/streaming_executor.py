"""
Real-time streaming executor for pentesting tools
Streams output line-by-line like ChatGPT
"""
import subprocess
import asyncio
from typing import AsyncGenerator, Dict, Any
from datetime import datetime
from app.utils.logger import logger


class StreamingToolExecutor:
    """Execute tools with real-time output streaming"""
    
    def __init__(self, tool_name: str, command: list, timeout: int = 300):
        self.tool_name = tool_name
        self.command = command
        self.timeout = timeout
        self.process = None
        self.start_time = None
        
    async def execute_streaming(self) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute tool and stream output line by line
        
        Yields:
            Dict with type, content, timestamp for each line
        """
        self.start_time = datetime.utcnow()
        
        try:
            # Send start event
            yield {
                "type": "tool_start",
                "tool": self.tool_name,
                "command": " ".join(self.command),
                "timestamp": self.start_time.isoformat()
            }
            
            logger.info(f"🚀 Starting streaming execution: {self.tool_name}")
            logger.info(f"   Command: {' '.join(self.command)}")
            
            # Start process with line buffering
            self.process = await asyncio.create_subprocess_exec(
                *self.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=1024 * 1024  # 1MB buffer
            )
            
            # Stream stdout in real-time
            line_count = 0
            async for line in self._read_stream(self.process.stdout):
                line_count += 1
                yield {
                    "type": "tool_output",
                    "tool": self.tool_name,
                    "content": line,
                    "line_number": line_count,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Small delay to prevent overwhelming
                await asyncio.sleep(0.01)
            
            # Wait for process to complete
            try:
                await asyncio.wait_for(self.process.wait(), timeout=self.timeout)
            except asyncio.TimeoutError:
                logger.error(f"⏱️ Tool {self.tool_name} timed out after {self.timeout}s")
                self.process.kill()
                yield {
                    "type": "tool_error",
                    "tool": self.tool_name,
                    "content": f"Timeout after {self.timeout} seconds",
                    "timestamp": datetime.utcnow().isoformat()
                }
                return
            
            # Get exit code
            exit_code = self.process.returncode
            
            # Read any stderr
            stderr = await self.process.stderr.read()
            stderr_text = stderr.decode('utf-8', errors='ignore').strip()
            
            # Send completion event
            execution_time = (datetime.utcnow() - self.start_time).total_seconds()
            
            yield {
                "type": "tool_complete",
                "tool": self.tool_name,
                "exit_code": exit_code,
                "execution_time": execution_time,
                "lines_output": line_count,
                "stderr": stderr_text if stderr_text else None,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"✅ Tool {self.tool_name} completed: exit_code={exit_code}, time={execution_time:.2f}s, lines={line_count}")
            
        except Exception as e:
            logger.error(f"❌ Streaming execution error for {self.tool_name}: {str(e)}", exc_info=True)
            yield {
                "type": "tool_error",
                "tool": self.tool_name,
                "content": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _read_stream(self, stream) -> AsyncGenerator[str, None]:
        """Read stream line by line"""
        while True:
            line = await stream.readline()
            if not line:
                break
            
            # Decode and clean line
            try:
                decoded = line.decode('utf-8', errors='ignore').rstrip()
                if decoded:  # Only yield non-empty lines
                    yield decoded
            except Exception as e:
                logger.warning(f"Failed to decode line: {e}")
                continue
    
    def kill(self):
        """Kill the running process"""
        if self.process and self.process.returncode is None:
            logger.warning(f"🛑 Killing process: {self.tool_name}")
            self.process.kill()

