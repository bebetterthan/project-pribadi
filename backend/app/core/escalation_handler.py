"""
Escalation Handler - Smart Flash → Pro Transitions

PURPOSE:
    Detect when Flash needs Pro's strategic intelligence and trigger escalation.
    Provides seamless handoff with full context preservation.

ESCALATION TRIGGERS:
    1. Critical finding detected (SQLi, RCE, etc.)
    2. Aggressive tool request (SQLMAP, FFUF on sensitive targets)
    3. Phase transition (recon → exploitation)
    4. Anomaly detected (unusual patterns)
    5. User requests deep analysis
"""
from typing import Dict, Any, Optional, Tuple
from enum import Enum
from app.utils.logger import logger
from app.core.pro_analyzer import ProStrategicAnalyzer
from app.core.model_selector import DecisionContext, EscalationTrigger


class EscalationReason(Enum):
    """Why escalation occurred"""
    CRITICAL_FINDING = "critical_finding"
    AGGRESSIVE_TOOL = "aggressive_tool_request"
    PHASE_TRANSITION = "phase_transition"
    ANOMALY = "anomaly_detected"
    USER_REQUEST = "user_request"
    COMPLEX_ERROR = "complex_error"


class EscalationHandler:
    """
    Manages Flash → Pro escalations with context preservation
    """
    
    def __init__(self, pro_analyzer: ProStrategicAnalyzer):
        """
        Initialize escalation handler
        
        Args:
            pro_analyzer: ProStrategicAnalyzer instance for Pro invocations
        """
        self.pro_analyzer = pro_analyzer
        self.escalation_count = 0
        self.escalation_history = []
        
        logger.info("📡 EscalationHandler initialized")
    
    def should_escalate(
        self,
        context: DecisionContext,
        **kwargs
    ) -> Tuple[bool, Optional[EscalationReason], str]:
        """
        Determine if escalation from Flash to Pro is needed
        
        Args:
            context: Decision context
            **kwargs: Additional context (severity, tool_name, findings_count, etc.)
        
        Returns:
            (should_escalate, reason, explanation)
        """
        # Use ModelSelector's trigger detection
        should_escalate, explanation = EscalationTrigger.should_escalate(
            context=context,
            finding_severity=kwargs.get('severity'),
            tool_name=kwargs.get('tool_name'),
            findings_count=kwargs.get('findings_count'),
            error_type=kwargs.get('error_type')
        )
        
        if not should_escalate:
            return False, None, explanation
        
        # Map to escalation reason
        if context == DecisionContext.CRITICAL_FINDING or kwargs.get('severity') in ['critical', 'high']:
            reason = EscalationReason.CRITICAL_FINDING
        elif context == DecisionContext.AGGRESSIVE_TOOL_REQUEST or kwargs.get('tool_name') in ['sqlmap', 'ffuf']:
            reason = EscalationReason.AGGRESSIVE_TOOL
        elif context == DecisionContext.PHASE_TRANSITION:
            reason = EscalationReason.PHASE_TRANSITION
        elif kwargs.get('findings_count', 0) > 500:
            reason = EscalationReason.ANOMALY
        else:
            reason = EscalationReason.USER_REQUEST
        
        return True, reason, explanation
    
    async def escalate_critical_finding(
        self,
        finding_type: str,
        finding_data: Dict[str, Any],
        target: str,
        scan_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Escalate critical finding to Pro for deep analysis
        
        Args:
            finding_type: Type of finding (sqli, rce, etc.)
            finding_data: Raw finding data
            target: Affected target
            scan_context: Scan context for Pro
        
        Returns:
            Pro's analysis result
        """
        self.escalation_count += 1
        logger.warning(f"🚨 ESCALATION #{self.escalation_count}: Critical finding → Pro analysis")
        logger.warning(f"   Type: {finding_type}")
        logger.warning(f"   Target: {target}")
        
        # Record escalation
        self.escalation_history.append({
            'reason': EscalationReason.CRITICAL_FINDING.value,
            'finding_type': finding_type,
            'target': target
        })
        
        # Invoke Pro analyzer
        analysis = await self.pro_analyzer.analyze_critical_finding(
            finding_type=finding_type,
            finding_data=finding_data,
            target=target,
            scan_context=scan_context
        )
        
        logger.info(f"✅ Pro analysis complete: {analysis.get('status')}")
        
        return {
            'escalation_id': self.escalation_count,
            'reason': EscalationReason.CRITICAL_FINDING.value,
            'pro_analysis': analysis,
            'verification_approved': analysis.get('verification_approved', False)
        }
    
    async def escalate_aggressive_tool(
        self,
        tool_name: str,
        target: str,
        evidence: Dict[str, Any],
        scan_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Escalate aggressive tool request to Pro for approval
        
        Args:
            tool_name: Tool requested (sqlmap, ffuf)
            target: Target for tool
            evidence: Evidence justifying tool usage
            scan_context: Current scan context
        
        Returns:
            Pro's approval decision
        """
        self.escalation_count += 1
        logger.warning(f"⚠️ ESCALATION #{self.escalation_count}: {tool_name.upper()} request → Pro approval")
        logger.warning(f"   Target: {target}")
        
        # Record escalation
        self.escalation_history.append({
            'reason': EscalationReason.AGGRESSIVE_TOOL.value,
            'tool_name': tool_name,
            'target': target
        })
        
        # Invoke Pro risk assessment
        assessment = await self.pro_analyzer.assess_aggressive_tool_request(
            tool_name=tool_name,
            target=target,
            evidence=evidence,
            scan_context=scan_context
        )
        
        if assessment.get('approved'):
            logger.info(f"✅ Pro APPROVED {tool_name.upper()} usage with constraints")
        else:
            logger.warning(f"❌ Pro DENIED {tool_name.upper()} usage")
        
        return {
            'escalation_id': self.escalation_count,
            'reason': EscalationReason.AGGRESSIVE_TOOL.value,
            'pro_assessment': assessment,
            'approved': assessment.get('approved', False),
            'constraints': assessment.get('constraints', {}),
            'risk_level': assessment.get('risk_level', 'high')
        }
    
    async def escalate_phase_transition(
        self,
        from_phase: str,
        to_phase: str,
        scan_results: Dict[str, Any],
        findings_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Escalate phase transition for Pro strategic decision
        
        Args:
            from_phase: Current phase (e.g., 'reconnaissance')
            to_phase: Proposed next phase (e.g., 'exploitation')
            scan_results: All scan results so far
            findings_summary: Summary of findings
        
        Returns:
            Pro's strategic decision
        """
        self.escalation_count += 1
        logger.info(f"📊 ESCALATION #{self.escalation_count}: Phase transition → Pro strategy")
        logger.info(f"   Transition: {from_phase} → {to_phase}")
        
        # Record escalation
        self.escalation_history.append({
            'reason': EscalationReason.PHASE_TRANSITION.value,
            'from_phase': from_phase,
            'to_phase': to_phase
        })
        
        # For now, approve transition (Pro analyzer would provide strategy)
        # This would integrate with Pro's generate_final_report or similar method
        logger.info(f"✅ Phase transition approved: {from_phase} → {to_phase}")
        
        return {
            'escalation_id': self.escalation_count,
            'reason': EscalationReason.PHASE_TRANSITION.value,
            'approved': True,
            'strategy': f"Proceeding to {to_phase} phase based on {from_phase} findings"
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get escalation statistics"""
        reason_counts = {}
        for esc in self.escalation_history:
            reason = esc['reason']
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        
        return {
            'total_escalations': self.escalation_count,
            'by_reason': reason_counts,
            'recent_escalations': self.escalation_history[-5:]  # Last 5
        }
    
    def log_summary(self):
        """Log escalation summary"""
        stats = self.get_statistics()
        
        logger.info("=" * 60)
        logger.info("📡 ESCALATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total escalations: {stats['total_escalations']}")
        logger.info(f"By reason: {stats['by_reason']}")
        logger.info("=" * 60)

