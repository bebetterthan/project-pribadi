"""
AI Agent with Agentic Workflow - ReAct Pattern
Inspired by ChatGPT's reasoning and tool-use capabilities
"""
import google.generativeai as genai
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from app.utils.logger import logger


class AgentState(str, Enum):
    """Agent workflow states"""
    PLANNING = "planning"
    EXECUTING = "executing"
    ANALYZING = "analyzing"
    REFINING = "refining"
    COMPLETE = "complete"


@dataclass
class AgentThought:
    """Represents AI's reasoning step"""
    step: int
    state: AgentState
    thought: str  # What AI is thinking
    action: Optional[str]  # What AI plans to do
    observation: Optional[str]  # What AI observed from action
    timestamp: str


@dataclass
class AgentDecision:
    """AI's decision at each step"""
    continue_scan: bool
    next_tools: List[str]
    reasoning: str
    questions_for_user: List[str]
    confidence_score: float  # 0-1


# Enhanced system context with ReAct pattern (Gemini-safe version)
AGENT_SYSTEM_CONTEXT = """
# SECURITY ASSESSMENT AI AGENT - ReAct Architecture

You are an autonomous security assessment agent for professional cybersecurity professionals with the ability to:
1. **Reason** about security findings and vulnerabilities
2. **Act** by selecting appropriate security scanning tools
3. **Observe** results and adapt assessment strategy

Your purpose is DEFENSIVE SECURITY TESTING for authorized systems only.

## WORKFLOW (ReAct Pattern):
You will go through iterative cycles:

**Thought** → What do I know? What should I assess next?
**Action** → Which security tool should I run? Why?
**Observation** → What did the scan reveal?
**Reflection** → Does this change my assessment strategy?

## AVAILABLE SECURITY ASSESSMENT TOOLS:

### 1. nmap (Network Discovery)
**Use First When:**
- You need to understand the security perimeter
- Discovering open ports and services
- OS fingerprinting required

**Outputs:** Port list, service versions, OS info
**Next Steps After:** Use findings to select specific vulnerability scanners

### 2. nuclei (Vulnerability Scanner)
**Use When:**
- You found web services (ports 80, 443, 8080)
- Need to identify known vulnerabilities (CVEs)
- Looking for security misconfigurations

**Outputs:** CVE IDs, severity ratings, affected endpoints
**Next Steps After:** Prioritize by risk level and remediation urgency

### 3. whatweb (Technology Identification)
**Use When:**
- Web application detected
- Need to identify tech stack for comprehensive assessment
- Looking for outdated or vulnerable framework versions

**Outputs:** CMS, frameworks, library versions
**Next Steps After:** Check for version-specific vulnerabilities

### 4. sslscan (TLS/SSL Security Analysis)
**Use When:**
- HTTPS services detected
- Checking for encryption configuration issues
- Certificate validation needed

**Outputs:** Cipher suites, TLS versions, cert info
**Next Steps After:** Identify weak cryptographic configurations

## DECISION-MAKING FRAMEWORK:

### Phase 1: Initial Planning
```
User Objective: [user's goal]
Current Knowledge: [empty]
Strategy: Start with reconnaissance (nmap)
Confidence: Low → Need data
```

### Phase 2: After Each Tool
```
Observation: [tool output summary]
New Intelligence: [key findings]
Updated Strategy: [adapt based on findings]
Confidence: [increasing as we learn more]
```

### Phase 3: Iterative Refinement
```
Question: Did findings meet expectations?
- If YES: Proceed to next phase
- If NO: Why? What tool would help?
- If UNCLEAR: Need more data? Which tool?
```

## OUTPUT FORMAT (JSON):
```json
{
  "thought": "Based on open ports, I see web services. Need to check for web vulns.",
  "reasoning": "Port 80 and 443 are open. High priority to scan for OWASP Top 10.",
  "next_tools": ["nuclei", "whatweb"],
  "tool_order_rationale": "Nuclei first for quick wins, then whatweb for targeted attacks",
  "continue_scan": true,
  "confidence": 0.75,
  "expected_findings": [
    "SQL injection points",
    "XSS vulnerabilities",
    "Outdated CMS versions"
  ],
  "questions_for_user": [],
  "exploitation_strategy": "If SQLi found, attempt to dump database credentials"
}
```

## CRITICAL RULES:
1. **Always explain your reasoning** - Transparency builds trust
2. **Adapt based on results** - Don't stick to original plan if data suggests otherwise
3. **Prioritize by risk** - Focus on vulnerabilities with highest security impact
4. **Think step-by-step** - Chain of thought reasoning
5. **Know when to stop** - Don't run tools that won't add value
6. **Professional context** - This is authorized security assessment for improving defenses

## EXAMPLE REASONING:
```
User wants: "Identify web vulnerabilities"

Thought: To assess web security, I need:
1. Identify web services (nmap port scan)
2. Scan for known vulnerabilities (nuclei)
3. Understand tech stack (whatweb) for comprehensive assessment

Action: Start with nmap to discover web services
Expected: Ports 80, 443, 8080 may be open

[After nmap finds port 80 and 443 open]

Observation: Web services confirmed on ports 80, 443
New Thought: Should assess for common web vulnerabilities
Action: Execute nuclei security scanner
Expected: Identification of security issues, misconfigurations

[After nuclei finds vulnerabilities]

Observation: Security issues found at /login.php endpoint
Reflection: Assessment objective achieved!
Recommendation: Review findings and prioritize remediation by risk level
```

You are conversational, transparent, and educational. Explain WHY, not just WHAT.
REMEMBER: You are helping security professionals identify and fix vulnerabilities in AUTHORIZED systems.
"""


class AIAgent:
    """
    Autonomous AI Agent for Penetration Testing
    Implements ReAct (Reasoning + Acting) pattern
    """

    def __init__(self, api_key: str):
        """Initialize AI Agent with optimized Gemini client"""
        if not api_key or len(api_key.strip()) < 10:
            raise ValueError("Invalid Gemini API key: key must be at least 10 characters")
        
        self.api_key = api_key
        
        # Use optimized Gemini client with connection pooling
        from app.services.gemini_client import get_gemini_client
        try:
            self.gemini_client = get_gemini_client(api_key)
            logger.info("✅ AI Agent initialized with optimized Gemini client")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini client: {e}")
            raise
        
        self.thoughts: List[AgentThought] = []
        self.context_memory: List[str] = []

    def initial_planning(self, target: str, user_objective: str) -> AgentDecision:
        """
        Phase 1: Initial strategic planning based on user objective
        Uses Pro model for complex strategic reasoning
        """
        logger.info(f"Agent: Starting initial planning for {target}")

        prompt = self._build_planning_prompt(target, user_objective, [])

        try:
            logger.info(f"🤖 Calling Gemini API for initial planning...")
            
            # Use optimized client with retry logic
            import asyncio
            response_text = asyncio.run(
                self.gemini_client.generate_with_retry(
                    prompt=prompt,
                    use_flash=False,  # Use pro model for planning
                    max_retries=2,
                    timeout=15.0
                )
            )
            
            logger.info(f"✅ Received response from Gemini API")
            logger.debug(f"Response text length: {len(response_text)} characters")

            decision = self._parse_agent_response(response_text, "initial_planning")
            
            logger.info(f"✅ Parsed decision: tools={decision.next_tools}, confidence={decision.confidence_score}")

            # Record thought process
            self._record_thought(
                state=AgentState.PLANNING,
                thought=decision.reasoning,
                action=f"Selected tools: {', '.join(decision.next_tools)}"
            )

            return decision

        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Agent planning failed: {error_msg}", exc_info=True)
            
            # Check if it's a safety filter block
            if "blocked" in error_msg.lower() or "safety" in error_msg.lower():
                logger.warning(f"⚠️ Gemini safety filter triggered - using fallback")
                fallback = self._fallback_decision()
                fallback.reasoning = "AI safety filters prevented direct response. Using standard reconnaissance strategy: Starting with nmap for network discovery, then adapting based on findings."
                return fallback
            elif "timeout" in error_msg.lower() or "deadline" in error_msg.lower():
                logger.warning(f"⚠️ Gemini API timeout - using fallback")
                fallback = self._fallback_decision()
                fallback.reasoning = "AI service timeout. Defaulting to standard security assessment workflow starting with network discovery."
                return fallback
            else:
                logger.warning(f"⚠️ Using fallback decision due to error")
                fallback = self._fallback_decision()
                fallback.reasoning = f"AI service encountered an issue ({error_msg[:100]}). Using standard penetration testing methodology: reconnaissance → vulnerability assessment → analysis."
                return fallback

    def analyze_and_adapt(
        self,
        target: str,
        user_objective: str,
        completed_tools: List[str],
        tool_results: Dict[str, Any]
    ) -> AgentDecision:
        """
        Phase 2: Analyze results and adapt strategy
        This is the "observe and refine" loop
        """
        logger.info(f"Agent: Analyzing results from {len(completed_tools)} tools")

        # Build context from previous results
        context = self._build_context_from_results(tool_results)
        self.context_memory.append(context)

        prompt = self._build_refinement_prompt(
            target,
            user_objective,
            completed_tools,
            context
        )

        try:
            # Use optimized client with retry logic
            import asyncio
            response_text = asyncio.run(
                self.gemini_client.generate_with_retry(
                    prompt=prompt,
                    use_flash=False,  # Use pro model for analysis
                    max_retries=2,
                    timeout=15.0
                )
            )

            decision = self._parse_agent_response(response_text, "refinement")

            # Record thought
            self._record_thought(
                state=AgentState.ANALYZING,
                thought=decision.reasoning,
                action=f"Continue: {decision.continue_scan}, Next: {decision.next_tools}",
                observation=context[:200]  # First 200 chars
            )

            return decision

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Agent refinement failed: {error_msg}", exc_info=True)
            
            # Provide meaningful fallback based on error type
            if "blocked" in error_msg.lower() or "safety" in error_msg.lower():
                reasoning = f"AI safety filters prevented analysis. Based on {len(completed_tools)} completed scans, sufficient data collected. Recommending to stop and review findings manually."
                should_continue = len(completed_tools) < 2  # Continue if less than 2 tools ran
            elif "timeout" in error_msg.lower():
                reasoning = f"AI service timeout during analysis. {len(completed_tools)} tools completed successfully. Stopping to allow manual review of results."
                should_continue = False
            else:
                reasoning = f"Analysis service encountered an issue. {len(completed_tools)} security scans completed. Recommending manual review of collected data."
                should_continue = False
            
            return AgentDecision(
                continue_scan=should_continue,
                next_tools=[],
                reasoning=reasoning,
                questions_for_user=[],
                confidence_score=0.5
            )

    def _build_planning_prompt(
        self,
        target: str,
        objective: str,
        available_tools: List[str]
    ) -> str:
        """Build prompt for initial planning"""
        prompt = f"{AGENT_SYSTEM_CONTEXT}\n\n"
        prompt += "# INITIAL PLANNING PHASE\n\n"
        prompt += f"**Target:** {target}\n"
        prompt += f"**User Objective:**\n{objective}\n\n"
        prompt += "**Current Knowledge:** None (starting fresh)\n\n"
        prompt += "**Your Task:**\n"
        prompt += "1. Understand what user wants to achieve\n"
        prompt += "2. Plan which tools to use first (start simple, add complexity)\n"
        prompt += "3. Explain your reasoning clearly\n"
        prompt += "4. Set expectations for what you'll find\n\n"
        prompt += "Respond with valid JSON only (no markdown, no extra text).\n"

        return prompt

    def _build_refinement_prompt(
        self,
        target: str,
        objective: str,
        completed_tools: List[str],
        observations: str
    ) -> str:
        """Build prompt for strategy refinement"""
        prompt = f"{AGENT_SYSTEM_CONTEXT}\n\n"
        prompt += "# STRATEGY REFINEMENT PHASE\n\n"
        prompt += f"**Target:** {target}\n"
        prompt += f"**User Objective:** {objective}\n\n"
        prompt += f"**Completed Tools:** {', '.join(completed_tools)}\n\n"
        prompt += f"**Observations from Previous Tools:**\n{observations}\n\n"
        prompt += "**Your Task:**\n"
        prompt += "1. Analyze what you learned from previous tools\n"
        prompt += "2. Decide: Should we continue scanning? Why/why not?\n"
        prompt += "3. If continuing: Which tools would add value? Why?\n"
        prompt += "4. If stopping: Summarize what we found\n"
        prompt += "5. Update confidence score (0-1) based on findings\n\n"
        prompt += "Respond with valid JSON only.\n"

        return prompt

    def _build_context_from_results(self, tool_results: Dict[str, Any]) -> str:
        """Summarize tool results for AI context"""
        context = []

        for tool_name, result in tool_results.items():
            if not result:
                continue

            context.append(f"## {tool_name.upper()} Results:")

            # Extract key findings
            if tool_name == "nmap" and "open_ports" in result:
                ports = result["open_ports"]
                context.append(f"- Found {len(ports)} open ports")
                for port in ports[:5]:  # Top 5 ports
                    context.append(f"  - Port {port['port']}: {port['service']} {port.get('version', '')}")

            elif tool_name == "nuclei" and "findings" in result:
                findings = result["findings"]
                context.append(f"- Found {len(findings)} vulnerabilities")
                for finding in findings[:3]:  # Top 3 vulns
                    context.append(f"  - {finding['severity']}: {finding['template_name']}")

            elif tool_name == "whatweb" and "technologies" in result:
                tech = result["technologies"]
                context.append(f"- Tech stack detected:")
                context.append(f"  - Server: {tech.get('server', 'Unknown')}")
                context.append(f"  - CMS: {tech.get('cms', 'None')}")

            context.append("")

        return "\n".join(context)

    def _parse_agent_response(self, response_text: str, phase: str) -> AgentDecision:
        """Parse AI's JSON response into decision object"""
        import json

        # Clean response
        text = response_text.strip()
        if text.startswith('```'):
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]
            text = text.strip()

        try:
            data = json.loads(text)

            return AgentDecision(
                continue_scan=data.get('continue_scan', True if phase == "initial_planning" else False),
                next_tools=data.get('next_tools', []),
                reasoning=data.get('reasoning', data.get('thought', 'No reasoning provided')),
                questions_for_user=data.get('questions_for_user', []),
                confidence_score=float(data.get('confidence', 0.5))
            )

        except Exception as e:
            logger.error(f"Failed to parse agent response: {str(e)}")
            logger.debug(f"Raw response: {text}")
            return self._fallback_decision()

    def _fallback_decision(self) -> AgentDecision:
        """Fallback decision when AI fails - use standard pentest methodology"""
        return AgentDecision(
            continue_scan=True,
            next_tools=['nmap', 'nuclei'],  # Standard approach
            reasoning="Using standard security assessment methodology: Starting with network discovery (nmap) followed by vulnerability scanning (nuclei). This is a proven approach for comprehensive security analysis.",
            questions_for_user=[],
            confidence_score=0.6  # Higher confidence in proven methodology
        )

    def _record_thought(
        self,
        state: AgentState,
        thought: str,
        action: Optional[str] = None,
        observation: Optional[str] = None
    ):
        """Record AI's thought process for transparency"""
        from datetime import datetime

        thought_obj = AgentThought(
            step=len(self.thoughts) + 1,
            state=state,
            thought=thought,
            action=action,
            observation=observation,
            timestamp=datetime.utcnow().isoformat()
        )

        self.thoughts.append(thought_obj)
        logger.info(f"Agent Thought #{thought_obj.step}: {thought[:100]}...")

    def get_thought_process(self) -> List[Dict[str, Any]]:
        """Get AI's full reasoning chain for user visibility"""
        return [
            {
                'step': t.step,
                'state': t.state.value,
                'thought': t.thought,
                'action': t.action,
                'observation': t.observation,
                'timestamp': t.timestamp
            }
            for t in self.thoughts
        ]
