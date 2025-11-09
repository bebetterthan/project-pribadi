"""
Model Orchestrator - Central Intelligence for Flash/Pro Model Management

Decides when to use Flash (fast, cheap) vs Pro (slow, expensive).
Manages escalations, cost tracking, and context sharing.

Philosophy:
- Flash: 80% of decisions, tactical execution
- Pro: 20% of decisions, strategic analysis
- Intelligent escalation based on complexity and severity
"""
from typing import Dict, Any, Optional, Callable
from loguru import logger
from enum import Enum
import time


class ModelType(Enum):
    """Model types available"""
    FLASH = "flash"
    PRO = "pro"


class EscalationTrigger(Enum):
    """Reasons to escalate from Flash to Pro"""
    CRITICAL_FINDING = "critical_finding"
    UNUSUAL_PATTERN = "unusual_pattern"
    PHASE_TRANSITION = "phase_transition"
    AGGRESSIVE_TOOL = "aggressive_tool"
    USER_REQUEST = "user_request"
    COMPLEX_DECISION = "complex_decision"
    HIGH_RISK = "high_risk"


class CostTracker:
    """Track API costs per scan"""
    
    # Estimated costs per call (approximate)
    FLASH_COST = 0.0001  # $0.0001 per Flash call
    PRO_COST = 0.001     # $0.001 per Pro call
    
    def __init__(self, budget_limit: float = 0.05):
        """
        Initialize cost tracker
        
        Args:
            budget_limit: Maximum budget per scan in USD (default: $0.05)
        """
        self.budget_limit = budget_limit
        self.flash_calls = 0
        self.pro_calls = 0
        self.start_time = time.time()
    
    def record_flash_call(self):
        """Record a Flash API call"""
        self.flash_calls += 1
    
    def record_pro_call(self):
        """Record a Pro API call"""
        self.pro_calls += 1
    
    @property
    def flash_cost(self) -> float:
        """Calculate Flash costs"""
        return self.flash_calls * self.FLASH_COST
    
    @property
    def pro_cost(self) -> float:
        """Calculate Pro costs"""
        return self.pro_calls * self.PRO_COST
    
    @property
    def total_cost(self) -> float:
        """Calculate total costs"""
        return self.flash_cost + self.pro_cost
    
    @property
    def budget_used_percentage(self) -> float:
        """Calculate percentage of budget used"""
        return (self.total_cost / self.budget_limit) * 100 if self.budget_limit > 0 else 0
    
    @property
    def budget_exhausted(self) -> bool:
        """Check if budget is exhausted"""
        return self.total_cost >= self.budget_limit
    
    @property
    def pro_budget_exhausted(self) -> bool:
        """Check if Pro budget specifically is exhausted (80% of total)"""
        pro_budget = self.budget_limit * 0.8
        return self.pro_cost >= pro_budget
    
    def get_summary(self) -> Dict[str, Any]:
        """Get cost summary"""
        elapsed = time.time() - self.start_time
        return {
            'flash_calls': self.flash_calls,
            'pro_calls': self.pro_calls,
            'flash_cost': f'${self.flash_cost:.4f}',
            'pro_cost': f'${self.pro_cost:.4f}',
            'total_cost': f'${self.total_cost:.4f}',
            'budget_limit': f'${self.budget_limit:.2f}',
            'budget_used': f'{self.budget_used_percentage:.1f}%',
            'elapsed_time': f'{elapsed:.1f}s',
            'flash_percentage': f'{(self.flash_calls / max(self.flash_calls + self.pro_calls, 1)) * 100:.1f}%',
            'pro_percentage': f'{(self.pro_calls / max(self.flash_calls + self.pro_calls, 1)) * 100:.1f}%'
        }


class ModelOrchestrator:
    """
    Model Orchestrator - Central intelligence for dual-model architecture.
    
    Responsibilities:
    1. Decide which model to use (Flash vs Pro)
    2. Track costs and enforce budgets
    3. Manage escalations from Flash to Pro
    4. Share context between models
    """
    
    def __init__(
        self,
        flash_engine,  # FlashTacticalEngine instance
        pro_analyzer,  # ProStrategicAnalyzer instance
        escalation_handler,  # EscalationHandler instance
        budget_limit: float = 0.05
    ):
        """
        Initialize orchestrator
        
        Args:
            flash_engine: FlashTacticalEngine for tactical decisions
            pro_analyzer: ProStrategicAnalyzer for strategic analysis
            escalation_handler: EscalationHandler for escalation logic
            budget_limit: Maximum budget per scan (default: $0.05)
        """
        self.flash = flash_engine
        self.pro = pro_analyzer
        self.escalation_handler = escalation_handler
        self.cost_tracker = CostTracker(budget_limit)
        
        # Current model in use
        self.current_model = ModelType.FLASH
        
        # Shared context between models
        self.shared_context = {
            'target': None,
            'target_type': None,
            'scan_phase': 'reconnaissance',
            'findings': {},
            'completed_tools': [],
            'pro_guidance': [],  # Strategic guidance from Pro
            'flash_notes': []    # Tactical notes from Flash
        }
        
        logger.info("🎯 ModelOrchestrator initialized")
        logger.info(f"   Budget: ${budget_limit:.3f}")
        logger.info(f"   Flash engine: {self.flash.model_name}")
        logger.info(f"   Pro analyzer: {self.pro.model_name}")
    
    def select_model(
        self,
        task_type: str,
        complexity: str = "low",
        severity: str = "low",
        force_pro: bool = False
    ) -> ModelType:
        """
        Decide which model to use for a task.
        
        Args:
            task_type: Type of task (tool_selection, analysis, strategy, etc.)
            complexity: Task complexity (low, medium, high)
            severity: Finding severity (low, medium, high, critical)
            force_pro: Force Pro usage regardless of other factors
        
        Returns:
            ModelType.FLASH or ModelType.PRO
        """
        # Check budget first
        if self.cost_tracker.budget_exhausted:
            logger.warning("💰 Total budget exhausted - using Flash only")
            return ModelType.FLASH
        
        if self.cost_tracker.pro_budget_exhausted and not force_pro:
            logger.warning("💰 Pro budget exhausted - using Flash only")
            return ModelType.FLASH
        
        # Force Pro if requested
        if force_pro:
            logger.info("🎯 Pro forced by caller")
            return ModelType.PRO
        
        # Decision matrix
        use_pro = False
        
        # Task type considerations
        if task_type in ['initial_strategy', 'final_report', 'phase_transition']:
            use_pro = True
            reason = f"Strategic task: {task_type}"
        
        elif task_type in ['critical_analysis', 'risk_assessment']:
            use_pro = True
            reason = f"Deep analysis required: {task_type}"
        
        elif task_type == 'aggressive_tool_approval':
            use_pro = True
            reason = "Aggressive tool requires Pro approval"
        
        # Complexity considerations
        elif complexity == 'high':
            use_pro = True
            reason = "High complexity task"
        
        # Severity considerations
        elif severity in ['high', 'critical']:
            use_pro = True
            reason = f"High severity: {severity}"
        
        # Default to Flash for routine tasks
        else:
            use_pro = False
            reason = "Routine task - Flash sufficient"
        
        selected = ModelType.PRO if use_pro else ModelType.FLASH
        
        if use_pro:
            logger.info(f"🎯 PRO selected: {reason}")
        else:
            logger.debug(f"⚡ FLASH selected: {reason}")
        
        return selected
    
    async def execute_with_model(
        self,
        model_type: ModelType,
        method_name: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a method with the specified model and track costs.
        
        Args:
            model_type: Which model to use
            method_name: Name of method to call
            **kwargs: Arguments to pass to method
        
        Returns:
            Result from the model
        """
        try:
            # Select engine
            if model_type == ModelType.PRO:
                engine = self.pro
                self.cost_tracker.record_pro_call()
                self.current_model = ModelType.PRO
            else:
                engine = self.flash
                self.cost_tracker.record_flash_call()
                self.current_model = ModelType.FLASH
            
            # Get method
            method = getattr(engine, method_name)
            
            # Execute
            start = time.time()
            result = await method(**kwargs)
            elapsed = time.time() - start
            
            logger.info(f"{'🎯' if model_type == ModelType.PRO else '⚡'} {model_type.value.upper()}.{method_name} completed in {elapsed:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ {model_type.value.upper()}.{method_name} failed: {e}")
            raise
    
    async def handle_escalation(
        self,
        trigger: EscalationTrigger,
        context: Dict[str, Any],
        event_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Handle escalation from Flash to Pro.
        
        Args:
            trigger: Why escalation is needed
            context: Context data for Pro
            event_callback: Optional callback for UI events
        
        Returns:
            Pro's analysis result
        """
        logger.warning(f"🚨 ESCALATION TRIGGERED: {trigger.value}")
        
        # Emit escalation event
        if event_callback:
            await event_callback({
                'type': 'escalation',
                'trigger': trigger.value,
                'reason': context.get('reason', 'Escalation required'),
                'severity': context.get('severity', 'medium')
            })
        
        # Decide which Pro method to call based on trigger
        if trigger == EscalationTrigger.CRITICAL_FINDING:
            result = await self.execute_with_model(
                ModelType.PRO,
                'analyze_critical_finding',
                finding=context.get('finding'),
                scan_context=context.get('scan_context')
            )
        
        elif trigger == EscalationTrigger.AGGRESSIVE_TOOL:
            result = await self.execute_with_model(
                ModelType.PRO,
                'assess_aggressive_tool_request',
                tool_name=context.get('tool_name'),
                target=context.get('target'),
                current_findings=context.get('findings'),
                reason=context.get('reason')
            )
        
        elif trigger == EscalationTrigger.PHASE_TRANSITION:
            # Generate phase analysis
            result = {
                'status': 'success',
                'analysis': f"Phase transition: {context.get('from_phase')} → {context.get('to_phase')}",
                'recommendation': 'Continue to next phase'
            }
        
        else:
            # Generic deep analysis
            result = {
                'status': 'success',
                'analysis': f"Escalation handled: {trigger.value}",
                'recommendation': 'Continue scan'
            }
        
        # Store Pro's guidance
        self.shared_context['pro_guidance'].append({
            'trigger': trigger.value,
            'timestamp': time.time(),
            'result': result
        })
        
        # Emit result event
        if event_callback:
            await event_callback({
                'type': 'pro_analysis',
                'content': result.get('analysis', ''),
                'metadata': {'trigger': trigger.value}
            })
        
        return result
    
    def update_context(self, updates: Dict[str, Any]):
        """Update shared context"""
        self.shared_context.update(updates)
        logger.debug(f"📋 Context updated: {list(updates.keys())}")
    
    def get_context(self) -> Dict[str, Any]:
        """Get current shared context"""
        return self.shared_context.copy()
    
    def get_cost_report(self) -> Dict[str, Any]:
        """Get detailed cost report"""
        summary = self.cost_tracker.get_summary()
        
        # Add model usage recommendation
        if self.cost_tracker.flash_calls == 0 and self.cost_tracker.pro_calls > 0:
            summary['recommendation'] = '⚠️ Only using Pro - consider using Flash for routine tasks'
        elif self.cost_tracker.pro_calls == 0 and self.cost_tracker.flash_calls > 0:
            summary['recommendation'] = '⚠️ Only using Flash - consider Pro for strategic decisions'
        elif self.cost_tracker.budget_used_percentage > 80:
            summary['recommendation'] = '⚠️ High budget usage - consider optimization'
        else:
            summary['recommendation'] = '✅ Good balance between Flash and Pro'
        
        return summary
    
    def reset(self):
        """Reset for new scan"""
        self.cost_tracker = CostTracker(self.cost_tracker.budget_limit)
        self.current_model = ModelType.FLASH
        self.shared_context = {
            'target': None,
            'target_type': None,
            'scan_phase': 'reconnaissance',
            'findings': {},
            'completed_tools': [],
            'pro_guidance': [],
            'flash_notes': []
        }
        logger.info("🔄 ModelOrchestrator reset for new scan")

