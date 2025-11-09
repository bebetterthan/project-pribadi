"""
Performance monitoring for tool execution
Tracks timing, resource usage, and bottlenecks
"""
import time
from typing import Dict, List, Any
from collections import defaultdict
from app.utils.logger import logger


class PerformanceMonitor:
    """Monitor and log performance metrics"""
    
    def __init__(self):
        self.timings: Dict[str, List[float]] = defaultdict(list)
        self.tool_counts: Dict[str, int] = defaultdict(int)
        self.start_times: Dict[str, float] = {}
    
    def start_tool(self, tool_name: str, context: str = ""):
        """Mark tool execution start"""
        key = f"{tool_name}_{context}" if context else tool_name
        self.start_times[key] = time.time()
        self.tool_counts[tool_name] += 1
        logger.debug(f"⏱️ Started: {tool_name} ({context})")
    
    def end_tool(self, tool_name: str, context: str = ""):
        """Mark tool execution end and record time"""
        key = f"{tool_name}_{context}" if context else tool_name
        
        if key in self.start_times:
            duration = time.time() - self.start_times[key]
            self.timings[tool_name].append(duration)
            del self.start_times[key]
            
            logger.debug(f"⏱️ Completed: {tool_name} in {duration:.2f}s")
            return duration
        return 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get performance statistics"""
        stats = {}
        
        for tool, times in self.timings.items():
            if times:
                stats[tool] = {
                    "count": len(times),
                    "total_time": sum(times),
                    "avg_time": sum(times) / len(times),
                    "min_time": min(times),
                    "max_time": max(times)
                }
        
        return stats
    
    def log_summary(self):
        """Log performance summary"""
        stats = self.get_statistics()
        
        if not stats:
            logger.info("📊 No performance data collected")
            return
        
        logger.info("=" * 60)
        logger.info("📊 PERFORMANCE SUMMARY")
        logger.info("=" * 60)
        
        total_time = sum(s["total_time"] for s in stats.values())
        logger.info(f"Total Execution Time: {total_time:.2f}s")
        logger.info("")
        
        for tool, data in sorted(stats.items(), key=lambda x: x[1]["total_time"], reverse=True):
            logger.info(f"{tool}:")
            logger.info(f"  Executions: {data['count']}")
            logger.info(f"  Total Time: {data['total_time']:.2f}s ({data['total_time']/total_time*100:.1f}%)")
            logger.info(f"  Avg Time: {data['avg_time']:.2f}s")
            logger.info(f"  Range: {data['min_time']:.2f}s - {data['max_time']:.2f}s")
            logger.info("")
        
        logger.info("=" * 60)


# Global instance
performance_monitor = PerformanceMonitor()

