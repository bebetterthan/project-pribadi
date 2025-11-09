"""
Hybrid Agent Router
Decides when to use Flash (cheap, fast) vs Pro (expensive, smart)
"""
from typing import Dict, Any, List, Optional, AsyncGenerator
from sqlalchemy.orm import Session
from app.services.function_calling_agent import FunctionCallingAgent
from app.models.scan import Scan
from app.utils.logger import logger
from datetime import datetime
import re


class HybridRouter:
    """
    Smart router that decides which model to use based on task complexity
    
    Strategy:
    - Flash (gemini-2.5-flash): Simple tasks, initial recon, data extraction
    - Pro (gemini-2.5-pro): Complex reasoning, correlation, strategic decisions
    """
    
    def __init__(self, gemini_api_key: str):
        self.api_key = gemini_api_key
        self.flash_agent = None
        self.pro_agent = None
        self.decision_log = []
    
    def analyze_complexity(self, user_prompt: str) -> str:
        """
        Analyze user prompt complexity to decide model
        
        Returns:
            'flash' or 'pro'
        """
        prompt_lower = user_prompt.lower()
        
        # Keywords that indicate need for Pro model (complex reasoning)
        pro_keywords = [
            'correlate', 'correlation',
            'chain', 'chaining',
            'exploit', 'exploitation path',
            'strategic', 'strategy',
            'prioritize', 'risk assessment',
            'compare', 'analyze relationship',
            'how to exploit', 'attack path',
            'recommend', 'advise',
            'complex', 'advanced'
        ]
        
        # Keywords that indicate Flash is sufficient (simple tasks)
        flash_keywords = [
            'scan', 'find', 'list',
            'check', 'test', 'verify',
            'identify', 'detect', 'discover',
            'what ports', 'which services',
            'enumerate', 'map'
        ]
        
        # Count matches
        pro_score = sum(1 for keyword in pro_keywords if keyword in prompt_lower)
        flash_score = sum(1 for keyword in flash_keywords if keyword in prompt_lower)
        
        # Length-based heuristic (long prompts = complex)
        if len(user_prompt) > 200:
            pro_score += 1
        
        # Multiple questions = complex
        question_marks = user_prompt.count('?')
        if question_marks > 2:
            pro_score += 1
        
        # Decision
        if pro_score > flash_score:
            decision = 'pro'
            reason = f"Complex reasoning needed (pro_score={pro_score} > flash_score={flash_score})"
        else:
            decision = 'flash'
            reason = f"Simple task suitable for Flash (flash_score={flash_score} >= pro_score={pro_score})"
        
        logger.info(f"🤖 Model Selection: {decision.upper()}")
        logger.info(f"   Reason: {reason}")
        
        self.decision_log.append({
            'decision': decision,
            'reason': reason,
            'pro_score': pro_score,
            'flash_score': flash_score
        })
        
        return decision
    
    async def run_hybrid_assessment(
        self,
        scan: Scan,
        db: Session,
        max_iterations: int = 10
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Run assessment with automatic model selection
        
        For most cases, use Flash. Only escalate to Pro if:
        1. User prompt indicates complex reasoning needed
        2. Flash agent explicitly requests Pro (future feature)
        """
        logger.info(f"🔀 Hybrid Router: Analyzing task complexity...")
        
        # Analyze complexity
        model_choice = self.analyze_complexity(scan.user_prompt or "General security assessment")
        
        # Yield router decision
        yield {
            "type": "system",
            "content": f"🤖 AI Router: Selected **{model_choice.upper()} model** for this assessment",
            "metadata": {
                "model": model_choice,
                "reason": self.decision_log[-1]['reason']
            }
        }
        
        # FASE 2: Initialize agent with hybrid_mode=True
        if not self.flash_agent:
            logger.info("⚡ Initializing Hybrid Agent (Flash + Pro)...")
            try:
                self.flash_agent = FunctionCallingAgent(self.api_key, use_pro_model=False, hybrid_mode=True)
                logger.info("✅ Hybrid Agent initialized successfully")
            except Exception as init_error:
                error_msg = str(init_error)
                error_type = type(init_error).__name__
                logger.error(f"❌ CRITICAL: Failed to initialize agent")
                logger.error(f"   Error type: {error_type}")
                logger.error(f"   Error message: {error_msg}")
                logger.error(f"   Full traceback:", exc_info=True)
                
                # Yield detailed error to frontend
                yield {
                    "type": "system",
                    "content": f"❌ **AI Agent Initialization Failed**\n\n"
                               f"**Error:** {error_msg}\n\n"
                               f"**Possible causes:**\n"
                               f"- Invalid or expired Gemini API key\n"
                               f"- API quota exceeded\n"
                               f"- Network/firewall blocking Google AI\n"
                               f"- Model name changed/deprecated\n\n"
                               f"**Solution:** Verify your API key at https://aistudio.google.com/app/apikey",
                    "metadata": {
                        "error": True,
                        "error_type": error_type,
                        "error_message": error_msg
                    }
                }
                return  # Stop execution
        
        agent = self.flash_agent
        
        # Run autonomous loop with error handling
        try:
            async for event in agent.run_autonomous_loop(scan, db, max_iterations):
                yield event
        except Exception as loop_error:
            import traceback
            import sys
            
            # CRITICAL: Write to FILE directly (bypass logger that crashes on emoji)
            error_details = f"""
{'='*80}
[ERROR] CRITICAL ERROR IN AGENT AUTONOMOUS LOOP
{'='*80}
Scan ID: {scan.id}
Target: {scan.target}
Error Type: {type(loop_error).__name__}
Error Message: {str(loop_error)}

Full Traceback:
{traceback.format_exc()}
{'='*80}
"""
            # Write to file DIRECTLY (no logger)
            try:
                with open("logs/CRITICAL_ERROR.txt", "a", encoding="utf-8") as f:
                    f.write(f"\n\n{'='*80}\n")
                    f.write(f"TIMESTAMP: {datetime.now().isoformat()}\n")
                    f.write(error_details)
                    f.flush()
            except:
                pass  # Don't let logging error crash the error handler
            
            print(error_details, flush=True)
            sys.stdout.flush()  # Force immediate flush
            
            # Log without emoji (ASCII only)
            logger.error(f"[ERROR] Error in agent autonomous loop: {str(loop_error)}", exc_info=True)
            yield {
                "type": "system",
                "content": f"❌ Agent execution error: {str(loop_error)}",
                "metadata": {"error": True, "error_type": type(loop_error).__name__}
            }
    
    def get_decision_log(self) -> List[Dict[str, Any]]:
        """Get history of routing decisions"""
        return self.decision_log


# ============================================================================
# SIMPLIFIED API
# ============================================================================

async def run_autonomous_scan(
    scan: Scan,
    db: Session,
    gemini_api_key: str,
    max_iterations: int = 10
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Simple API for running autonomous scan with hybrid routing
    
    Usage:
        async for event in run_autonomous_scan(scan, db, api_key):
            # Stream event to frontend via SSE
            yield event
    """
    router = HybridRouter(gemini_api_key)
    
    async for event in router.run_hybrid_assessment(scan, db, max_iterations):
        yield event

