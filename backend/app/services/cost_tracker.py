"""
Cost Tracker for Hybrid Agent (Fase 2)
Tracks token usage and calculates cost savings from hybrid routing
"""
from typing import Dict, List, Any
from datetime import datetime
from app.utils.logger import logger


# Gemini Pricing (as of 2025 - Update if Google changes pricing)
# Prices are per 1 Million tokens
PRICING = {
    "flash": {
        "input": 0.075,   # $0.075 per 1M input tokens
        "output": 0.30,   # $0.30 per 1M output tokens
        "name": "Gemini 2.5 Flash"
    },
    "pro": {
        "input": 1.25,    # $1.25 per 1M input tokens
        "output": 5.00,   # $5.00 per 1M output tokens
        "name": "Gemini 2.5 Pro"
    }
}


class CostTracker:
    """
    Track token usage and cost for hybrid agent
    
    Features:
    - Per-call token tracking
    - Cost calculation with real pricing
    - Savings analysis (hybrid vs all-Pro vs all-Flash)
    - Detailed cost breakdown
    """
    
    def __init__(self, scan_id: str):
        """
        Initialize cost tracker for a scan session
        
        Args:
            scan_id: Scan ID to track
        """
        self.scan_id = scan_id
        self.calls = []  # List of all API calls
        self.total_flash_calls = 0
        self.total_pro_calls = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        
        logger.info(f"💰 CostTracker initialized for scan {scan_id}")
    
    def record_call(
        self,
        model_type: str,  # "flash" or "pro"
        input_tokens: int,
        output_tokens: int,
        task_type: str = None,
        response_time: float = 0.0
    ):
        """
        Record an API call with token usage
        
        Args:
            model_type: "flash" or "pro"
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            task_type: Optional task type for analytics
            response_time: Optional response time in seconds
        """
        call_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "model_type": model_type,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "task_type": task_type,
            "response_time": response_time,
            "cost": self._calculate_cost(model_type, input_tokens, output_tokens)
        }
        
        self.calls.append(call_record)
        
        # Update counters
        if model_type == "flash":
            self.total_flash_calls += 1
        else:
            self.total_pro_calls += 1
        
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        
        logger.debug(f"📊 Recorded {model_type.upper()} call: {input_tokens}in + {output_tokens}out tokens = ${call_record['cost']:.6f}")
    
    def _calculate_cost(self, model_type: str, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost for a single call
        
        Args:
            model_type: "flash" or "pro"
            input_tokens: Input token count
            output_tokens: Output token count
            
        Returns:
            Cost in USD
        """
        pricing = PRICING.get(model_type, PRICING["pro"])  # Default to Pro if unknown
        
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        
        return input_cost + output_cost
    
    def get_total_cost(self) -> float:
        """
        Get total actual cost (hybrid mode)
        
        Returns:
            Total cost in USD
        """
        return sum(call["cost"] for call in self.calls)
    
    def get_estimated_all_flash_cost(self) -> float:
        """
        Estimate cost if all calls were Flash
        
        Returns:
            Estimated cost in USD
        """
        total_cost = 0.0
        for call in self.calls:
            cost = self._calculate_cost("flash", call["input_tokens"], call["output_tokens"])
            total_cost += cost
        return total_cost
    
    def get_estimated_all_pro_cost(self) -> float:
        """
        Estimate cost if all calls were Pro
        
        Returns:
            Estimated cost in USD
        """
        total_cost = 0.0
        for call in self.calls:
            cost = self._calculate_cost("pro", call["input_tokens"], call["output_tokens"])
            total_cost += cost
        return total_cost
    
    def get_savings_percentage(self) -> float:
        """
        Calculate savings percentage vs all-Pro
        
        Returns:
            Savings percentage (0-100)
        """
        all_pro = self.get_estimated_all_pro_cost()
        actual = self.get_total_cost()
        
        if all_pro == 0:
            return 0.0
        
        savings = ((all_pro - actual) / all_pro) * 100
        return max(0.0, savings)  # Can't have negative savings
    
    def get_cost_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive cost report (Fase 2 requirement)
        
        Returns:
            Dict with detailed cost analysis
        """
        actual_cost = self.get_total_cost()
        all_flash_cost = self.get_estimated_all_flash_cost()
        all_pro_cost = self.get_estimated_all_pro_cost()
        savings = self.get_savings_percentage()
        
        # Model usage breakdown
        flash_tokens = sum(
            call["input_tokens"] + call["output_tokens"] 
            for call in self.calls if call["model_type"] == "flash"
        )
        pro_tokens = sum(
            call["input_tokens"] + call["output_tokens"] 
            for call in self.calls if call["model_type"] == "pro"
        )
        
        report = {
            "scan_id": self.scan_id,
            "total_calls": len(self.calls),
            "flash_calls": self.total_flash_calls,
            "pro_calls": self.total_pro_calls,
            
            "tokens": {
                "total_input": self.total_input_tokens,
                "total_output": self.total_output_tokens,
                "total": self.total_input_tokens + self.total_output_tokens,
                "flash_tokens": flash_tokens,
                "pro_tokens": pro_tokens
            },
            
            "costs": {
                "actual_usd": round(actual_cost, 6),
                "estimated_all_flash_usd": round(all_flash_cost, 6),
                "estimated_all_pro_usd": round(all_pro_cost, 6)
            },
            
            "savings": {
                "vs_all_pro_usd": round(all_pro_cost - actual_cost, 6),
                "vs_all_pro_percentage": round(savings, 2),
                "vs_all_flash_usd": round(actual_cost - all_flash_cost, 6)
            },
            
            "model_ratio": {
                "flash_percentage": round((self.total_flash_calls / len(self.calls) * 100), 1) if self.calls else 0,
                "pro_percentage": round((self.total_pro_calls / len(self.calls) * 100), 1) if self.calls else 0
            },
            
            "call_details": self.calls
        }
        
        return report
    
    def get_summary_text(self) -> str:
        """
        Get human-readable summary text for display
        
        Returns:
            Formatted summary string
        """
        report = self.get_cost_report()
        
        text = f"""
💰 **Cost Analysis**

**Actual Cost:** ${report['costs']['actual_usd']:.4f}
**Model Usage:**
  - Flash: {report['flash_calls']} calls ({report['model_ratio']['flash_percentage']}%)
  - Pro: {report['pro_calls']} calls ({report['model_ratio']['pro_percentage']}%)

**Comparison:**
  - All-Flash: ${report['costs']['estimated_all_flash_usd']:.4f}
  - All-Pro: ${report['costs']['estimated_all_pro_usd']:.4f}

**💡 Savings:** ${report['savings']['vs_all_pro_usd']:.4f} ({report['savings']['vs_all_pro_percentage']:.1f}% vs All-Pro)

**Token Usage:**
  - Input: {report['tokens']['total_input']:,}
  - Output: {report['tokens']['total_output']:,}
  - Total: {report['tokens']['total']:,}
"""
        return text.strip()
    
    def log_summary(self):
        """Log cost summary to console"""
        logger.info("="*60)
        logger.info(f"💰 COST SUMMARY - Scan {self.scan_id}")
        logger.info("="*60)
        report = self.get_cost_report()
        logger.info(f"Total Calls: {report['total_calls']} (Flash: {report['flash_calls']}, Pro: {report['pro_calls']})")
        logger.info(f"Actual Cost: ${report['costs']['actual_usd']:.6f}")
        logger.info(f"All-Pro Cost: ${report['costs']['estimated_all_pro_usd']:.6f}")
        logger.info(f"Savings: ${report['savings']['vs_all_pro_usd']:.6f} ({report['savings']['vs_all_pro_percentage']:.1f}%)")
        logger.info(f"Tokens: {report['tokens']['total']:,} (Input: {report['tokens']['total_input']:,}, Output: {report['tokens']['total_output']:,})")
        logger.info("="*60)

