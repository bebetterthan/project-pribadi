import google.generativeai as genai
from typing import Dict, Any, List
from dataclasses import dataclass
from app.utils.logger import logger


@dataclass
class AIStrategy:
    """AI strategic planning result"""
    tools_needed: List[str]
    reasoning: str
    attack_plan: str
    expected_findings: List[str]


PLANNER_SYSTEM_CONTEXT = """
# AI PENTESTING AGENT - STRATEGIC PLANNER

You are an elite penetration testing strategist. Your job is to analyze the user's objective and create an optimal tool selection and attack strategy.

## AVAILABLE TOOLS:
1. **nmap** - Port scanning, service detection, OS fingerprinting
   - Use for: Initial reconnaissance, finding open ports/services
   - Output: Open ports, service versions, OS detection

2. **nuclei** - Automated vulnerability scanning with templates
   - Use for: Finding known CVEs, misconfigurations, exposed files
   - Output: CVE findings, severity ratings, proof-of-concept URLs

3. **whatweb** - Web technology identification
   - Use for: Identifying CMS, frameworks, JavaScript libraries
   - Output: Technology stack, versions, plugins

4. **sslscan** - SSL/TLS security analysis
   - Use for: Finding weak ciphers, certificate issues, SSL vulnerabilities
   - Output: Certificate info, cipher suites, SSL/TLS versions

## YOUR TASK:
Based on user's objective, determine:
1. Which tools to use (in optimal order)
2. Why each tool is necessary
3. What specific information you expect to find
4. How findings will chain together for exploitation

## RESPONSE FORMAT (JSON):
```json
{
  "tools_needed": ["tool1", "tool2"],
  "reasoning": "Detailed explanation of tool selection and order",
  "attack_plan": "Step-by-step strategy based on expected findings",
  "expected_findings": ["What to look for", "Key indicators", "Exploitation targets"]
}
```

## RULES:
- Select MINIMUM tools needed (don't waste time/resources)
- Order tools logically (reconnaissance → vulnerability → exploitation)
- Consider stealth vs noise tradeoff
- Think like an attacker: what info leads to compromise?
"""


class AIPlannerService:
    """AI service for strategic planning and tool selection"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=api_key)
        # Use latest fast model for quick strategy planning
        self.model = genai.GenerativeModel(
            'gemini-2.0-flash-exp',
            generation_config={
                'temperature': 0.4,
                'max_output_tokens': 4096,
            }
        )

    def plan_attack_strategy(self, target: str, user_objective: str) -> AIStrategy:
        """Generate strategic plan based on user's objective"""

        prompt = f"{PLANNER_SYSTEM_CONTEXT}\n\n"
        prompt += f"# PLANNING REQUEST\n\n"
        prompt += f"**Target:** {target}\n"
        prompt += f"**User Objective:**\n{user_objective}\n\n"
        prompt += "Analyze the objective and create optimal tool selection strategy.\n"
        prompt += "Respond ONLY with valid JSON (no markdown, no extra text)."

        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.3,  # More deterministic for planning
                    'max_output_tokens': 2048,
                }
            )

            # Parse JSON response
            import json
            response_text = response.text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            strategy_data = json.loads(response_text)

            # Validate tools
            valid_tools = ['nmap', 'nuclei', 'whatweb', 'sslscan']
            tools_needed = [t for t in strategy_data['tools_needed'] if t in valid_tools]

            if not tools_needed:
                # Fallback: use all tools if AI didn't provide valid ones
                logger.warning("AI didn't provide valid tools, using all tools as fallback")
                tools_needed = valid_tools

            logger.info(f"AI Strategy: Selected {len(tools_needed)} tools - {', '.join(tools_needed)}")

            return AIStrategy(
                tools_needed=tools_needed,
                reasoning=strategy_data.get('reasoning', 'Strategic tool selection'),
                attack_plan=strategy_data.get('attack_plan', 'Execute tools in sequence'),
                expected_findings=strategy_data.get('expected_findings', [])
            )

        except Exception as e:
            logger.error(f"AI planning failed: {str(e)}")
            # Fallback: use all tools
            return AIStrategy(
                tools_needed=['nmap', 'nuclei', 'whatweb', 'sslscan'],
                reasoning=f"Using all tools due to planning error: {str(e)}",
                attack_plan="Execute comprehensive scan with all available tools",
                expected_findings=["Port information", "Vulnerabilities", "Technology stack", "SSL/TLS issues"]
            )
