"""
Metrics endpoint for monitoring and observability
Prometheus-compatible metrics
"""
from fastapi import APIRouter, Response
from fastapi.responses import PlainTextResponse
from typing import Dict, Any
import time
from collections import defaultdict
import threading

from app.config import settings
from app.utils.logger import logger

router = APIRouter()

# ============================================================================
# Metrics Storage (In-Memory)
# ============================================================================

class MetricsCollector:
    """
    Thread-safe metrics collector
    
    Stores metrics in memory for Prometheus scraping.
    For production, consider using prometheus_client library.
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        self._counters = defaultdict(int)
        self._gauges = defaultdict(float)
        self._histograms = defaultdict(list)
        self._start_time = time.time()
    
    def increment_counter(self, name: str, labels: Dict[str, str] = None, value: int = 1):
        """Increment a counter metric"""
        key = self._make_key(name, labels)
        with self._lock:
            self._counters[key] += value
    
    def set_gauge(self, name: str, labels: Dict[str, str] = None, value: float = 0):
        """Set a gauge metric"""
        key = self._make_key(name, labels)
        with self._lock:
            self._gauges[key] = value
    
    def observe_histogram(self, name: str, labels: Dict[str, str] = None, value: float = 0):
        """Add observation to histogram"""
        key = self._make_key(name, labels)
        with self._lock:
            self._histograms[key].append(value)
    
    def _make_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """Create metric key with labels"""
        if not labels:
            return name
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def get_metrics_text(self) -> str:
        """Export metrics in Prometheus text format"""
        lines = []
        
        # Add metadata
        lines.append(f"# HELP app_info Application information")
        lines.append(f"# TYPE app_info gauge")
        lines.append(f'app_info{{version="{settings.VERSION}",environment="{settings.ENVIRONMENT}"}} 1')
        lines.append("")
        
        # Uptime
        uptime = int(time.time() - self._start_time)
        lines.append(f"# HELP app_uptime_seconds Application uptime in seconds")
        lines.append(f"# TYPE app_uptime_seconds gauge")
        lines.append(f"app_uptime_seconds {uptime}")
        lines.append("")
        
        with self._lock:
            # Counters
            if self._counters:
                lines.append("# Counters")
                for key, value in sorted(self._counters.items()):
                    name = key.split("{")[0]
                    lines.append(f"# HELP {name} Total count")
                    lines.append(f"# TYPE {name} counter")
                    lines.append(f"{key} {value}")
                lines.append("")
            
            # Gauges
            if self._gauges:
                lines.append("# Gauges")
                for key, value in sorted(self._gauges.items()):
                    name = key.split("{")[0]
                    lines.append(f"# HELP {name} Current value")
                    lines.append(f"# TYPE {name} gauge")
                    lines.append(f"{key} {value}")
                lines.append("")
            
            # Histograms (simplified - just show count, sum, avg)
            if self._histograms:
                lines.append("# Histograms")
                for key, values in sorted(self._histograms.items()):
                    name = key.split("{")[0]
                    if values:
                        count = len(values)
                        total = sum(values)
                        avg = total / count if count > 0 else 0
                        
                        lines.append(f"# HELP {name} Histogram")
                        lines.append(f"# TYPE {name} summary")
                        lines.append(f"{key}_count {count}")
                        lines.append(f"{key}_sum {total}")
                        lines.append(f"{key}_avg {avg}")
                lines.append("")
        
        return "\n".join(lines)
    
    def reset(self):
        """Reset all metrics (for testing)"""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()


# Global metrics collector
metrics_collector = MetricsCollector()


# ============================================================================
# Metrics API
# ============================================================================

def record_scan_started(scan_id: str, target: str):
    """Record that a scan has started"""
    metrics_collector.increment_counter("scans_started_total")
    metrics_collector.increment_counter("scans_active", value=1)


def record_scan_completed(scan_id: str, duration_seconds: float, success: bool):
    """Record scan completion"""
    metrics_collector.increment_counter("scans_completed_total", labels={"status": "success" if success else "failed"})
    metrics_collector.increment_counter("scans_active", value=-1)
    metrics_collector.observe_histogram("scan_duration_seconds", value=duration_seconds)


def record_tool_execution(tool_name: str, duration_seconds: float, success: bool):
    """Record tool execution"""
    metrics_collector.increment_counter(
        "tool_executions_total",
        labels={"tool": tool_name, "status": "success" if success else "failed"}
    )
    metrics_collector.observe_histogram(
        "tool_execution_duration_seconds",
        labels={"tool": tool_name},
        value=duration_seconds
    )


def record_api_call(model: str, input_tokens: int, output_tokens: int, duration_seconds: float):
    """Record Gemini API call"""
    metrics_collector.increment_counter("gemini_api_calls_total", labels={"model": model})
    metrics_collector.increment_counter("gemini_api_tokens_total", labels={"model": model, "type": "input"}, value=input_tokens)
    metrics_collector.increment_counter("gemini_api_tokens_total", labels={"model": model, "type": "output"}, value=output_tokens)
    metrics_collector.observe_histogram("gemini_api_duration_seconds", labels={"model": model}, value=duration_seconds)


def record_error(error_type: str, component: str):
    """Record error occurrence"""
    metrics_collector.increment_counter("errors_total", labels={"type": error_type, "component": component})


def set_active_scans(count: int):
    """Set current number of active scans"""
    metrics_collector.set_gauge("scans_active", value=count)


def set_circuit_breaker_state(name: str, state: str):
    """Set circuit breaker state"""
    # Convert state to numeric: closed=0, half_open=1, open=2
    state_value = {"closed": 0, "half_open": 1, "open": 2}.get(state, -1)
    metrics_collector.set_gauge("circuit_breaker_state", labels={"name": name}, value=state_value)


# ============================================================================
# Endpoint
# ============================================================================

@router.get("/metrics", response_class=PlainTextResponse, tags=["monitoring"])
async def get_metrics():
    """
    Prometheus-compatible metrics endpoint
    
    Returns metrics in Prometheus text format for scraping.
    """
    if not settings.METRICS_ENABLED:
        return PlainTextResponse(
            content="# Metrics disabled\n",
            status_code=200
        )
    
    metrics_text = metrics_collector.get_metrics_text()
    return PlainTextResponse(content=metrics_text, status_code=200)


@router.get("/metrics/summary", tags=["monitoring"])
async def get_metrics_summary():
    """
    Human-readable metrics summary (JSON format)
    
    Useful for dashboards and debugging.
    """
    if not settings.METRICS_ENABLED:
        return {"message": "Metrics disabled"}
    
    with metrics_collector._lock:
        return {
            "counters": dict(metrics_collector._counters),
            "gauges": dict(metrics_collector._gauges),
            "histograms": {
                key: {
                    "count": len(values),
                    "sum": sum(values),
                    "avg": sum(values) / len(values) if values else 0,
                    "min": min(values) if values else 0,
                    "max": max(values) if values else 0
                }
                for key, values in metrics_collector._histograms.items()
            }
        }


# Export metrics collector for use in other modules
__all__ = [
    "router",
    "metrics_collector",
    "record_scan_started",
    "record_scan_completed",
    "record_tool_execution",
    "record_api_call",
    "record_error",
    "set_active_scans",
    "set_circuit_breaker_state"
]

