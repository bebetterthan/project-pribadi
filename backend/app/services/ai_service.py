import google.generativeai as genai
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class AIAnalysisResult:
    analysis_text: str
    prompt_tokens: int
    completion_tokens: int
    model_used: str
    cost_usd: float
    prompt_text: str  # Store full prompt for transparency


# Gemini 1.5 Flash pricing (as of 2024)
GEMINI_FLASH_PRICING = {
    'input': 0.075 / 1_000_000,   # $0.075 per 1M tokens
    'output': 0.30 / 1_000_000,   # $0.30 per 1M tokens
}

SYSTEM_CONTEXT = """
# AI PENTESTING AGENT - SYSTEM PERSONA

You are an elite penetration testing agent with expertise in:
- 🎯 OSCP/OSCE certified offensive security techniques
- 🔍 APT (Advanced Persistent Threat) tactics, techniques, and procedures
- 💻 Web application hacking (OWASP Top 10+)
- 🌐 Network penetration testing and lateral movement
- 🔓 Exploitation framework mastery (Metasploit, Empire, Cobalt Strike)
- 🛡️ Evasion techniques and AV/EDR bypass methods

## YOUR MISSION:
Analyze scan results to create a **strategic penetration testing roadmap** that maximizes compromise while minimizing detection.

## ANALYSIS FRAMEWORK:

### 1. TACTICAL ASSESSMENT (Quick Win Analysis)
- Identify the **easiest path to initial access**
- Prioritize by: Exploitability > Impact > Stealth
- Consider: authentication bypass, default credentials, known CVEs with public exploits

### 2. STRATEGIC EXPLOITATION PLAN
For each vulnerability, provide:
- **Attack Vector**: Exact method and entry point
- **Exploit Commands**: Copy-paste ready terminal commands
- **Expected Outcome**: What access/data you'll gain
- **Detection Risk**: Low/Medium/High (based on common SIEM/IDS rules)
- **Privilege Escalation Path**: How to go from low to SYSTEM/root

### 3. ADVANCED TECHNIQUES
- **Chaining vulnerabilities**: Combine multiple issues for maximum impact
- **Living off the land**: Use built-in tools (PowerShell, certutil, wmic)
- **Persistence mechanisms**: How to maintain access
- **Data exfiltration**: Techniques to extract sensitive information

### 4. INTELLIGENCE GATHERING
- Technology stack weaknesses and known CVEs
- Misconfigurations and security gaps
- Potential credential harvesting opportunities
- Social engineering attack vectors

### 5. FALSE POSITIVE FILTERING
- Identify scan results that are likely false positives
- Explain technical reasoning (e.g., "Port closed on firewall but scanner detected service")

### 6. REMEDIATION ROADMAP
- **Critical fixes** (within 24 hours)
- **High priority** (within 1 week)
- **Medium priority** (within 1 month)
- Specific commands/configurations to implement

## OUTPUT STYLE:
- Use military-style briefing format (clear, actionable, numbered)
- Include code blocks with ```bash or ```python for commands
- Add MITRE ATT&CK technique IDs (e.g., T1003.001)
- Reference CVE IDs and CVSS scores
- Think like an attacker, but explain like a teacher

## IMPORTANT:
- NO generic security advice ("keep systems updated" ❌)
- YES specific exploitation steps ("Use this exact curl command to exploit SQLi" ✅)
- Focus on what works NOW, not theoretical attacks
- Consider real-world constraints (IDS/IPS, WAF, rate limiting)
"""


class AIService:
    """AI service for analyzing scan results using Google Gemini"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=api_key)
        # Use latest experimental model for heavy analysis and complex reasoning
        self.model = genai.GenerativeModel(
            'gemini-2.0-flash-exp',
            generation_config={
                'temperature': 0.2,
                'max_output_tokens': 8192,
            }
        )

    def analyze_scan_results(self, scan_data: Dict[str, Any]) -> AIAnalysisResult:
        """Analyze aggregated scan results and generate insights"""
        prompt = self._build_analysis_prompt(scan_data)

        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.2,  # Low temp for analytical tasks
                    'max_output_tokens': 4096,
                }
            )

            usage = response.usage_metadata
            cost = self._calculate_cost(
                usage.prompt_token_count,
                usage.candidates_token_count
            )

            return AIAnalysisResult(
                analysis_text=response.text,
                prompt_tokens=usage.prompt_token_count,
                completion_tokens=usage.candidates_token_count,
                model_used='gemini-exp-1206',
                cost_usd=cost,
                prompt_text=prompt  # Store for transparency
            )
        except Exception as e:
            raise Exception(f"AI analysis failed: {str(e)}")

    def _build_analysis_prompt(self, scan_data: Dict[str, Any]) -> str:
        """Build comprehensive prompt from scan results"""
        target = scan_data['target']
        tools = scan_data['tools']

        prompt = SYSTEM_CONTEXT + "\n\n"
        prompt += f"# Penetration Test Analysis\n\n"
        prompt += f"**Target:** {target}\n"
        prompt += f"**Scan Date:** {scan_data['timestamp']}\n"
        prompt += f"**Tools Used:** {', '.join(tools)}\n\n"

        # Add Nmap results
        if 'nmap' in scan_data['results']:
            nmap = scan_data['results']['nmap']
            prompt += "## Nmap Scan Results\n\n"

            if nmap.get('open_ports'):
                prompt += f"**Open Ports:** {len(nmap['open_ports'])}\n\n"
                for port in nmap['open_ports']:
                    prompt += f"- **Port {port['port']}/{port['protocol']}**: "
                    prompt += f"{port['service']} {port['version']}\n"

            if nmap.get('os_detection'):
                prompt += f"\n**OS Detection:** {nmap['os_detection']}\n"

            prompt += "\n"

        # Add Nuclei results
        if 'nuclei' in scan_data['results']:
            nuclei = scan_data['results']['nuclei']
            prompt += "## Nuclei Vulnerability Scan\n\n"

            if nuclei.get('findings'):
                prompt += f"**Vulnerabilities Found:** {nuclei['total_findings']}\n\n"
                for finding in nuclei['findings'][:10]:  # Limit to top 10
                    prompt += f"### {finding['template_name']}\n"
                    prompt += f"- **ID:** {finding['template_id']}\n"
                    prompt += f"- **Severity:** {finding['severity']}\n"
                    prompt += f"- **Matched At:** {finding['matched_at']}\n"
                    if finding.get('cve_id'):
                        prompt += f"- **CVE:** {finding['cve_id']}\n"
                    if finding.get('description'):
                        prompt += f"- **Description:** {finding['description']}\n"
                    prompt += "\n"
            else:
                prompt += "No vulnerabilities detected by Nuclei templates.\n\n"

        # Add whatweb results
        if 'whatweb' in scan_data['results']:
            whatweb = scan_data['results']['whatweb']
            if 'technologies' in whatweb:
                tech = whatweb['technologies']
                prompt += "## Technology Stack (whatweb)\n\n"
                prompt += f"- **Web Server:** {tech.get('server', 'Unknown')}\n"
                prompt += f"- **CMS:** {tech.get('cms', 'Not detected')}\n"
                prompt += f"- **Programming Language:** {tech.get('language', 'Unknown')}\n"
                if tech.get('js_frameworks'):
                    prompt += f"- **JavaScript Frameworks:** {', '.join(tech['js_frameworks'])}\n"
                prompt += "\n"

        # Add sslscan results
        if 'sslscan' in scan_data['results']:
            sslscan = scan_data['results']['sslscan']
            prompt += "## SSL/TLS Analysis (sslscan)\n\n"

            if sslscan.get('certificate'):
                cert = sslscan['certificate']
                prompt += f"- **Certificate Valid:** {cert.get('valid', 'N/A')}\n"

            if sslscan.get('weak_ciphers'):
                prompt += f"- **Weak Ciphers:** {len(sslscan['weak_ciphers'])}\n"

            if sslscan.get('vulnerabilities'):
                prompt += f"- **Known Vulnerabilities:** {', '.join(sslscan['vulnerabilities'])}\n"

            prompt += "\n"

        # Analysis instructions
        prompt += """
# Analysis Request

Based on the scan results above, provide a comprehensive penetration testing analysis with the following structure:

## 1. Executive Summary
- One paragraph overview of target's security posture
- Overall risk rating (Critical/High/Medium/Low)

## 2. Critical Findings (Top 3)
For each critical finding:
- **Vulnerability Name & CVE** (if applicable)
- **Exploitability Assessment** (Easy/Medium/Hard)
- **Business Impact** (What attacker can achieve)
- **Exploitation Steps** (Step-by-step with specific commands)
- **Remediation** (Exact steps to fix)

## 3. Additional Vulnerabilities
- List medium/low severity findings (brief)

## 4. Attack Path Recommendations
- Suggest next steps for deeper pentesting
- Specific tools/techniques to try manually

## 5. False Positives Assessment
- Identify likely false positives and explain why

Format your response in **markdown** with proper headers and code blocks for commands.
Use ```bash for shell commands and ```python for scripts.
"""

        return prompt

    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate estimated cost in USD"""
        input_cost = prompt_tokens * GEMINI_FLASH_PRICING['input']
        output_cost = completion_tokens * GEMINI_FLASH_PRICING['output']
        return round(input_cost + output_cost, 6)
