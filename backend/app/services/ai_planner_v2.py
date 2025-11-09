"""
AI Planner v2 - Template-based approach for safety
Separates abstract planning from concrete execution

Strategy: AI never sees real targets, only generates abstract strategies
"""
import google.generativeai as genai
from typing import List, Dict, Any
from dataclasses import dataclass
from app.utils.logger import logger
import json


@dataclass
class SecurityAssessmentPlan:
    """Abstract security assessment plan (no target info)"""
    objective: str
    recommended_tools: List[str]
    tool_order_rationale: str
    expected_finding_types: List[str]
    confidence: float


# SAFE PROMPT - No target, no red flags
SAFE_PLANNER_PROMPT = """
# SECURITY ASSESSMENT STRATEGY ADVISOR

You are a cybersecurity assessment strategy advisor helping professionals plan authorized security audits.

## YOUR ROLE:
Recommend which security assessment tools to use based on the user's objective, WITHOUT knowing specific targets.

## AVAILABLE TOOLS:
1. **nmap** - Network service discovery and port scanning
2. **nuclei** - Vulnerability detection with templates  
3. **whatweb** - Web technology identification
4. **sslscan** - TLS/SSL configuration analysis

## RULES:
- Recommend tools based on OBJECTIVE, not target
- Explain WHY each tool is useful
- Suggest optimal order of execution
- Predict what types of findings to expect

## OUTPUT FORMAT (JSON only):
```json
{
  "objective_analysis": "Brief analysis of what user wants",
  "recommended_tools": ["tool1", "tool2"],
  "tool_order_rationale": "Why this order makes sense",
  "expected_finding_types": ["Finding type 1", "Finding type 2"],
  "confidence": 0.85
}
```

## EXAMPLES:

**User Objective:** "Check for web vulnerabilities"
**Your Response:**
```json
{
  "objective_analysis": "User wants comprehensive web security assessment",
  "recommended_tools": ["nmap", "nuclei", "whatweb"],
  "tool_order_rationale": "Start with nmap to discover web services, use nuclei to find vulnerabilities, whatweb to identify outdated tech stack",
  "expected_finding_types": ["Open ports with web services", "Common web vulnerabilities (XSS, SQLi, etc)", "Outdated framework versions"],
  "confidence": 0.88
}
```

**User Objective:** "Find network exposure"
**Your Response:**
```json
{
  "objective_analysis": "User wants to understand network attack surface",
  "recommended_tools": ["nmap"],
  "tool_order_rationale": "Single comprehensive nmap scan sufficient to map network exposure",
  "expected_finding_types": ["Open ports", "Service versions", "OS fingerprint"],
  "confidence": 0.92
}
```

CRITICAL: 
- NEVER ask for specific target information
- Focus on METHODOLOGY, not targets
- This is for AUTHORIZED security assessment only
"""


class SafeAIPlanner:
    """
    Safe AI Planner that uses template-based approach
    AI never sees real targets, only objectives
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            'gemini-2.0-flash-exp',
            generation_config={
                'temperature': 0.4,
                'max_output_tokens': 2048,
            }
        )
    
    def create_assessment_plan(self, user_objective: str) -> SecurityAssessmentPlan:
        """
        Create abstract security assessment plan without target info
        
        Args:
            user_objective: What user wants to achieve (NO target names!)
        
        Returns:
            SecurityAssessmentPlan with recommended tools and strategy
        """
        logger.info(f"🧠 Creating safe assessment plan for objective: {user_objective[:100]}")
        
        # Build safe prompt
        prompt = f"{SAFE_PLANNER_PROMPT}\n\n"
        prompt += "# USER REQUEST\n\n"
        prompt += f"**User Objective:** {user_objective}\n\n"
        prompt += "Analyze this objective and recommend appropriate security assessment tools.\n"
        prompt += "Respond ONLY with valid JSON (no markdown, no explanation)."
        
        try:
            logger.info("🤖 Calling Gemini API (safe mode - no target info)...")
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            logger.info(f"✅ Received safe response from AI")
            logger.debug(f"Response length: {len(response_text)} chars")
            
            # Parse JSON
            # Remove markdown code blocks if present
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            data = json.loads(response_text)
            
            # Validate required fields
            required = ['recommended_tools', 'tool_order_rationale', 'confidence']
            for field in required:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Create plan object
            plan = SecurityAssessmentPlan(
                objective=user_objective,
                recommended_tools=data['recommended_tools'],
                tool_order_rationale=data['tool_order_rationale'],
                expected_finding_types=data.get('expected_finding_types', []),
                confidence=float(data['confidence'])
            )
            
            logger.info(f"✅ Plan created: {plan.recommended_tools}")
            logger.info(f"💭 Rationale: {plan.tool_order_rationale[:150]}...")
            
            return plan
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse AI response as JSON: {e}")
            logger.debug(f"Raw response: {response_text}")
            return self._fallback_plan(user_objective)
        except Exception as e:
            logger.error(f"❌ Safe planner failed: {e}", exc_info=True)
            return self._fallback_plan(user_objective)
    
    def _fallback_plan(self, objective: str) -> SecurityAssessmentPlan:
        """Fallback plan when AI fails"""
        logger.warning("⚠️ Using fallback assessment plan")
        
        # Smart fallback based on keywords in objective
        tools = ['nmap']  # Always start with nmap
        
        if any(word in objective.lower() for word in ['web', 'http', 'site', 'vuln']):
            tools.extend(['nuclei', 'whatweb'])
            rationale = "Standard web security assessment: Network discovery → Vulnerability scanning → Technology identification"
        elif 'ssl' in objective.lower() or 'tls' in objective.lower():
            tools.append('sslscan')
            rationale = "TLS/SSL security assessment: Network discovery → SSL analysis"
        else:
            tools.append('nuclei')
            rationale = "General security assessment: Network discovery → Vulnerability detection"
        
        return SecurityAssessmentPlan(
            objective=objective,
            recommended_tools=tools,
            tool_order_rationale=rationale,
            expected_finding_types=[
                "Network services and open ports",
                "Security vulnerabilities",
                "Configuration issues"
            ],
            confidence=0.70
        )


class SafeAIAnalyzer:
    """
    Safe AI Analyzer for results
    Receives SANITIZED results (no target info in sensitive data)
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            'gemini-2.0-flash-exp',
            generation_config={
                'temperature': 0.3,
                'max_output_tokens': 4096,
            }
        )
    
    def analyze_results(
        self, 
        objective: str,
        completed_tools: List[str],
        sanitized_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze scan results in a safe way
        
        Args:
            objective: User's goal
            completed_tools: Which tools ran
            sanitized_results: Results with TARGET_HOST placeholders
        
        Returns:
            Analysis with recommendations
        """
        logger.info(f"🧠 Analyzing results from {len(completed_tools)} tools (safe mode)")
        
        # Build safe analysis prompt
        prompt = "# SECURITY ASSESSMENT RESULTS ANALYSIS\n\n"
        prompt += "You are analyzing results from authorized security assessment tools.\n\n"
        prompt += f"**Original Objective:** {objective}\n\n"
        prompt += f"**Tools Executed:** {', '.join(completed_tools)}\n\n"
        prompt += "**Results Summary:**\n\n"
        
        # Add sanitized results
        for tool, result in sanitized_results.items():
            prompt += f"## {tool.upper()} Results:\n"
            if isinstance(result, dict):
                if 'open_ports' in result:
                    prompt += f"- Found {len(result['open_ports'])} open ports\n"
                if 'findings' in result:
                    prompt += f"- Found {len(result['findings'])} security findings\n"
                if 'technologies' in result:
                    prompt += f"- Identified technology stack\n"
            prompt += "\n"
        
        prompt += "\n**Your Task:**\n"
        prompt += "1. Analyze if the objective was met\n"
        prompt += "2. Decide if more scanning is needed\n"
        prompt += "3. Provide security recommendations\n\n"
        prompt += "Respond with JSON:\n"
        prompt += '{"objective_met": true/false, "continue_scanning": true/false, '
        prompt += '"reasoning": "...", "next_tools": [...], "recommendations": [...]}'
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Parse JSON
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            analysis = json.loads(response_text)
            logger.info(f"✅ Analysis complete: objective_met={analysis.get('objective_met')}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}")
            return {
                "objective_met": len(completed_tools) >= 2,
                "continue_scanning": False,
                "reasoning": f"Completed {len(completed_tools)} security scans. Recommend manual review.",
                "next_tools": [],
                "recommendations": ["Review findings manually", "Prioritize by severity"]
            }

