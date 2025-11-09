"""
LLM Cost Tracking
Monitor token usage and estimated costs
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict


@dataclass
class CostEntry:
    """Single cost tracking entry"""
    timestamp: datetime
    model: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    request_type: str = "generation"  # generation, function_call, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)


class CostTracker:
    """
    Track LLM costs and token usage
    
    Features:
    - Per-model cost tracking
    - Time-based aggregation (hourly, daily)
    - Budget warnings
    - Cost forecasting
    """
    
    def __init__(self, budget_limit_usd: Optional[float] = None):
        """
        Initialize cost tracker
        
        Args:
            budget_limit_usd: Optional budget limit for warnings
        """
        self.entries: List[CostEntry] = []
        self.budget_limit = budget_limit_usd
        
        # Quick access stats
        self.total_cost = 0.0
        self.total_tokens = 0
        self.request_count = 0
        
        # Per-model stats
        self.model_stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "requests": 0,
                "tokens": 0,
                "cost": 0.0
            }
        )
    
    def track_request(
        self,
        model: str,
        provider: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost_usd: float,
        request_type: str = "generation",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Track a single LLM request
        
        Args:
            model: Model name
            provider: Provider name
            prompt_tokens: Input token count
            completion_tokens: Output token count
            cost_usd: Cost in USD
            request_type: Type of request
            metadata: Additional metadata
        """
        total_tokens = prompt_tokens + completion_tokens
        
        entry = CostEntry(
            timestamp=datetime.utcnow(),
            model=model,
            provider=provider,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            request_type=request_type,
            metadata=metadata or {}
        )
        
        self.entries.append(entry)
        
        # Update totals
        self.total_cost += cost_usd
        self.total_tokens += total_tokens
        self.request_count += 1
        
        # Update model stats
        self.model_stats[model]["requests"] += 1
        self.model_stats[model]["tokens"] += total_tokens
        self.model_stats[model]["cost"] += cost_usd
        
        # Check budget
        if self.budget_limit and self.total_cost > self.budget_limit:
            self._trigger_budget_warning()
    
    def get_total_cost(self) -> float:
        """Get total cost in USD"""
        return round(self.total_cost, 4)
    
    def get_total_tokens(self) -> int:
        """Get total token count"""
        return self.total_tokens
    
    def get_model_breakdown(self) -> Dict[str, Dict[str, Any]]:
        """
        Get cost breakdown by model
        
        Returns:
            Dict mapping model name to stats
        """
        return dict(self.model_stats)
    
    def get_time_series(
        self,
        granularity: str = "hour",
        window_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get time-series cost data
        
        Args:
            granularity: "hour" or "day"
            window_hours: Time window in hours
            
        Returns:
            List of time buckets with costs
        """
        cutoff = datetime.utcnow() - timedelta(hours=window_hours)
        recent_entries = [e for e in self.entries if e.timestamp > cutoff]
        
        # Group by time bucket
        buckets: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"tokens": 0, "cost": 0.0, "requests": 0}
        )
        
        for entry in recent_entries:
            if granularity == "hour":
                bucket_key = entry.timestamp.strftime("%Y-%m-%d %H:00")
            else:  # day
                bucket_key = entry.timestamp.strftime("%Y-%m-%d")
            
            buckets[bucket_key]["tokens"] += entry.total_tokens
            buckets[bucket_key]["cost"] += entry.cost_usd
            buckets[bucket_key]["requests"] += 1
        
        # Convert to sorted list
        result = [
            {
                "timestamp": key,
                "tokens": data["tokens"],
                "cost": round(data["cost"], 4),
                "requests": data["requests"]
            }
            for key, data in sorted(buckets.items())
        ]
        
        return result
    
    def get_daily_summary(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get daily cost summary for last N days"""
        return self.get_time_series(granularity="day", window_hours=days * 24)
    
    def get_budget_status(self) -> Dict[str, Any]:
        """
        Get budget status
        
        Returns:
            Budget info with warnings
        """
        if not self.budget_limit:
            return {
                "has_budget": False,
                "message": "No budget limit set"
            }
        
        remaining = self.budget_limit - self.total_cost
        percent_used = (self.total_cost / self.budget_limit) * 100
        
        if percent_used >= 100:
            status = "exceeded"
            message = f"Budget exceeded by ${abs(remaining):.2f}"
        elif percent_used >= 90:
            status = "critical"
            message = f"Budget 90% used, ${remaining:.2f} remaining"
        elif percent_used >= 75:
            status = "warning"
            message = f"Budget 75% used, ${remaining:.2f} remaining"
        else:
            status = "ok"
            message = f"${remaining:.2f} of ${self.budget_limit:.2f} remaining"
        
        return {
            "has_budget": True,
            "budget_limit": self.budget_limit,
            "total_cost": round(self.total_cost, 2),
            "remaining": round(remaining, 2),
            "percent_used": round(percent_used, 1),
            "status": status,
            "message": message
        }
    
    def forecast_cost(self, estimated_tokens: int, model: str) -> Dict[str, Any]:
        """
        Forecast cost for estimated token usage
        
        Args:
            estimated_tokens: Estimated token count
            model: Model to use
            
        Returns:
            Cost forecast
        """
        # Get average cost per token for this model
        if model in self.model_stats:
            avg_cost_per_token = (
                self.model_stats[model]["cost"] / 
                self.model_stats[model]["tokens"]
                if self.model_stats[model]["tokens"] > 0
                else 0.0
            )
        else:
            # Use overall average
            avg_cost_per_token = (
                self.total_cost / self.total_tokens
                if self.total_tokens > 0
                else 0.0
            )
        
        estimated_cost = estimated_tokens * avg_cost_per_token
        
        return {
            "estimated_tokens": estimated_tokens,
            "estimated_cost_usd": round(estimated_cost, 4),
            "avg_cost_per_token": round(avg_cost_per_token, 6),
            "model": model
        }
    
    def export_report(self) -> Dict[str, Any]:
        """
        Export comprehensive cost report
        
        Returns:
            Full cost report
        """
        return {
            "summary": {
                "total_cost_usd": round(self.total_cost, 4),
                "total_tokens": self.total_tokens,
                "total_requests": self.request_count,
                "avg_cost_per_request": round(
                    self.total_cost / self.request_count if self.request_count > 0 else 0,
                    4
                ),
                "avg_tokens_per_request": (
                    self.total_tokens // self.request_count if self.request_count > 0 else 0
                )
            },
            "by_model": self.get_model_breakdown(),
            "budget": self.get_budget_status(),
            "recent_activity": self.get_time_series(granularity="hour", window_hours=24),
            "daily_summary": self.get_daily_summary(days=7)
        }
    
    def reset(self) -> None:
        """Reset all tracking data"""
        self.entries = []
        self.total_cost = 0.0
        self.total_tokens = 0
        self.request_count = 0
        self.model_stats.clear()
    
    def _trigger_budget_warning(self) -> None:
        """Trigger budget warning (can be extended to send alerts)"""
        status = self.get_budget_status()
        print(f"⚠️ BUDGET WARNING: {status['message']}")
