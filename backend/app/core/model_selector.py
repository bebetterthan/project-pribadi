"""
Model Selector - Intelligent Flash vs Pro Decision Making

PURPOSE:
    Smart orchestration between Flash 2.5 (tactical) and Pro 2.5 (strategic)
    for optimal cost-performance balance.

ARCHITECTURE:
    Flash: 80% of decisions (fast, cheap, tactical)
    Pro: 20% of decisions (smart, strategic, complex)
"""
from typing import Dict, Any, Optional, Literal
from enum import Enum
from app.utils.logger import logger


class ModelType(Enum):
    """AI model types"""
    FLASH = "flash-2.5"
    PRO = "pro-2.5"


class DecisionContext(Enum):
    """Decision context types"""
    # Tactical (Flash)
    TOOL_SELECTION = "tool_selection"
    PROGRESS_UPDATE = "progress_update"
    BASIC_PATTERN = "basic_pattern"
    ROUTINE_ERROR = "routine_error"
    FUNCTION_CALL = "function_call"
    
    # Strategic (Pro)
    INITIAL_STRATEGY = "initial_strategy"
    CRITICAL_FINDING = "critical_finding"
    PHASE_TRANSITION = "phase_transition"
    RISK_ASSESSMENT = "risk_assessment"
    AGGRESSIVE_TOOL_REQUEST = "aggressive_tool_request"
    FINAL_REPORTING = "final_reporting"
    ANOMALY_DETECTION = "anomaly_detection"
    DEEP_ANALYSIS = "deep_analysis"


class EscalationTrigger:
    """Escalation trigger detection"""
    
    @staticmethod
    def should_escalate(
        context: DecisionContext,
        finding_severity: Optional[str] = None,
        tool_name: Optional[str] = None,
        findings_count: Optional[int] = None,
        error_type: Optional[str] = None
    ) -> tuple[bool, str]:
        """
        Determine if Flash should escalate to Pro
        
        Returns:
            (should_escalate: bool, reason: str)
        """
        # Strategic contexts ALWAYS use Pro
        strategic_contexts = {
            DecisionContext.INITIAL_STRATEGY,
            DecisionContext.CRITICAL_FINDING,
            DecisionContext.PHASE_TRANSITION,
            DecisionContext.RISK_ASSESSMENT,
            DecisionContext.AGGRESSIVE_TOOL_REQUEST,
            DecisionContext.FINAL_REPORTING,
            DecisionContext.DEEP_ANALYSIS
        }
        
        if context in strategic_contexts:
            return True, f"Strategic decision: {context.value}"
        
        # Trigger 1: Critical Finding Detected
        if finding_severity in ['critical', 'high']:
            return True, f"Critical finding detected: {finding_severity} severity"
        
        # Trigger 2: Aggressive Tool Request (SQLMAP, FFUF)
        aggressive_tools = ['sqlmap', 'ffuf']
        if tool_name and tool_name.lower() in aggressive_tools:
            return True, f"Aggressive tool requires Pro approval: {tool_name}"
        
        # Trigger 3: Anomaly Detection (unusual patterns)
        if findings_count and findings_count > 500:
            return True, f"Anomaly: Unusually high findings count ({findings_count})"
        
        # Trigger 4: Complex Error
        if error_type and error_type in ['authentication', 'authorization', 'rate_limit']:
            return True, f"Complex error requires strategic handling: {error_type}"
        
        # Default: Flash handles it
        return False, "Routine tactical decision"


class ModelSelector:
    """
    Intelligent model selector with cost tracking
    
    Decides when to use Flash (cheap/fast) vs Pro (smart/expensive)
    """
    
    def __init__(self):
        self.flash_calls = 0
        self.pro_calls = 0
        self.flash_cost = 0.0001  # Per call estimate
        self.pro_cost = 0.001     # Per call estimate (10x)
        self.escalation_history = []
        
        logger.info("🧠 ModelSelector initialized")
        logger.info(f"   Flash cost: ${self.flash_cost}/call")
        logger.info(f"   Pro cost: ${self.pro_cost}/call (10x)")
    
    def select_model(
        self,
        context: DecisionContext,
        **kwargs
    ) -> tuple[ModelType, str]:
        """
        Select appropriate model for decision
        
        Args:
            context: Decision context (tool selection, critical finding, etc.)
            **kwargs: Additional context (severity, tool_name, etc.)
        
        Returns:
            (model_type, reasoning)
        """
        should_use_pro, reason = EscalationTrigger.should_escalate(
            context=context,
            finding_severity=kwargs.get('severity'),
            tool_name=kwargs.get('tool_name'),
            findings_count=kwargs.get('findings_count'),
            error_type=kwargs.get('error_type')
        )
        
        if should_use_pro:
            self.pro_calls += 1
            self.escalation_history.append({
                'context': context.value,
                'reason': reason,
                'model': 'pro'
            })
            logger.info(f"🎯 PRO selected: {reason}")
            return ModelType.PRO, reason
        else:
            self.flash_calls += 1
            logger.debug(f"⚡ FLASH selected: {reason}")
            return ModelType.FLASH, reason
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get usage statistics"""
        total_calls = self.flash_calls + self.pro_calls
        if total_calls == 0:
            return {
                'flash_calls': 0,
                'pro_calls': 0,
                'total_calls': 0,
                'flash_percentage': 0,
                'pro_percentage': 0,
                'estimated_cost': 0
            }
        
        flash_pct = (self.flash_calls / total_calls) * 100
        pro_pct = (self.pro_calls / total_calls) * 100
        estimated_cost = (self.flash_calls * self.flash_cost) + (self.pro_calls * self.pro_cost)
        
        return {
            'flash_calls': self.flash_calls,
            'pro_calls': self.pro_calls,
            'total_calls': total_calls,
            'flash_percentage': flash_pct,
            'pro_percentage': pro_pct,
            'estimated_cost': estimated_cost,
            'escalations': len(self.escalation_history)
        }
    
    def log_summary(self):
        """Log usage summary"""
        stats = self.get_statistics()
        
        logger.info("=" * 60)
        logger.info("🧠 MODEL USAGE SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Flash calls: {stats['flash_calls']} ({stats['flash_percentage']:.1f}%)")
        logger.info(f"Pro calls: {stats['pro_calls']} ({stats['pro_percentage']:.1f}%)")
        logger.info(f"Total calls: {stats['total_calls']}")
        logger.info(f"Estimated cost: ${stats['estimated_cost']:.4f}")
        logger.info(f"Escalations: {stats['escalations']}")
        logger.info("=" * 60)
        
        # Log escalation reasons
        if self.escalation_history:
            logger.info("\n📊 ESCALATION HISTORY:")
            for i, esc in enumerate(self.escalation_history[-5:], 1):  # Last 5
                logger.info(f"  {i}. {esc['context']}: {esc['reason']}")

