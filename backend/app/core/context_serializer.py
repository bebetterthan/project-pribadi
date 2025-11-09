"""
Context Serializer - Safe Context Transfer for Hybrid Mode

PURPOSE:
    Convert Flash model context into Pro-consumable text format
    WITHOUT triggering Gemini SDK protobuf bugs.

KEY PRINCIPLE:
    NEVER transfer chat history or schemas.
    ONLY transfer data as structured text.
"""
from typing import Dict, Any, List
from datetime import datetime
import json


class ContextSerializer:
    """
    Serializes Flash reconnaissance context into Pro-safe Markdown format
    
    This is the CRITICAL component that prevents '\n description' errors
    by ensuring NO direct context transfer between models.
    """
    
    @staticmethod
    def serialize(
        target: str,
        tool_results: Dict[str, Any],
        findings: Dict[str, Any],
        flash_analysis: str = None
    ) -> str:
        """
        Convert Flash context to structured text document
        
        Args:
            target: Scan target (domain/IP)
            tool_results: Raw outputs from tools
            findings: Structured findings from Flash
            flash_analysis: Flash model's analysis text
            
        Returns:
            Markdown-formatted context document (JSON-safe string)
            
        Requirements:
            - Output MUST be pure text (no objects)
            - Output MUST be JSON-safe (no literal newlines in keys)
            - Output MUST be comprehensive (no data loss)
            - Output MUST be structured (Markdown sections)
        """
        sections = []
        
        # Header
        sections.append("# Security Assessment Context")
        sections.append(f"\n## Target Information")
        sections.append(f"- **Domain/IP**: {target}")
        sections.append(f"- **Assessment Type**: Comprehensive Security Audit")
        sections.append(f"- **Timestamp**: {datetime.utcnow().isoformat()}Z")
        sections.append(f"- **Phase**: Reconnaissance Complete (Flash Model)")
        
        # Reconnaissance Phase Summary
        sections.append("\n## Reconnaissance Phase Summary")
        sections.append("\n### Executive Summary")
        
        # Generate executive summary from findings
        exec_summary = ContextSerializer._generate_executive_summary(findings)
        sections.append(exec_summary)
        
        # Tool Results (detailed)
        sections.append("\n## Tool Execution Results")
        
        # Subdomain Enumeration
        if 'subfinder' in tool_results:
            sections.append(ContextSerializer._format_subfinder_results(
                tool_results['subfinder'], 
                findings.get('subdomains', {})
            ))
        
        # Port Scanning
        if 'nmap' in tool_results:
            sections.append(ContextSerializer._format_nmap_results(
                tool_results['nmap'],
                findings.get('ports', {})
            ))
        
        # HTTP Probing
        if 'httpx' in tool_results:
            sections.append(ContextSerializer._format_httpx_results(
                tool_results['httpx'],
                findings.get('http_services', {})
            ))
        
        # Technology Detection
        if 'whatweb' in tool_results:
            sections.append(ContextSerializer._format_whatweb_results(
                tool_results['whatweb'],
                findings.get('technologies', {})
            ))
        
        # Risk Profile
        sections.append("\n## Risk Profile Summary")
        sections.append(ContextSerializer._format_risk_profile(findings))
        
        # Flash Analysis
        if flash_analysis:
            sections.append("\n## Initial Analysis (Flash Model)")
            sections.append(f"\n{flash_analysis}")
        
        # Recommended Next Steps
        sections.append("\n## Recommended Next Steps")
        sections.append(ContextSerializer._generate_recommendations(findings))
        
        # Appendix (raw data - truncated)
        sections.append("\n## Appendix: Raw Tool Outputs (Excerpts)")
        sections.append(ContextSerializer._format_raw_outputs(tool_results))
        
        # Join all sections
        context_document = "\n".join(sections)
        
        # CRITICAL: Ensure JSON-safe (escape any problematic characters)
        context_document = ContextSerializer._make_json_safe(context_document)
        
        return context_document
    
    @staticmethod
    def _generate_executive_summary(findings: Dict[str, Any]) -> str:
        """Generate executive summary from findings"""
        lines = []
        
        # Subdomain count
        subdomain_count = len(findings.get('subdomains', {}).get('list', []))
        if subdomain_count > 0:
            lines.append(f"- **Subdomains Discovered**: {subdomain_count}")
        
        # Open ports
        open_ports = findings.get('ports', {}).get('open_ports', [])
        if open_ports:
            lines.append(f"- **Open Ports**: {len(open_ports)} ports found")
            
            # Highlight critical ports
            critical_ports = [p for p in open_ports if p.get('port') in [3306, 5432, 27017, 6379, 1433]]
            if critical_ports:
                lines.append(f"  - **CRITICAL**: Database ports exposed ({', '.join(str(p.get('port')) for p in critical_ports)})")
        
        # Services
        services = findings.get('services', [])
        if services:
            lines.append(f"- **Services Identified**: {len(services)} services")
        
        # Technologies
        tech_count = len(findings.get('technologies', {}).get('list', []))
        if tech_count > 0:
            lines.append(f"- **Technologies Detected**: {tech_count} different technologies")
        
        # Overall risk
        risk_level = findings.get('risk_level', 'MEDIUM')
        lines.append(f"- **Initial Risk Assessment**: **{risk_level}**")
        
        return "\n".join(lines) if lines else "No significant findings in reconnaissance phase."
    
    @staticmethod
    def _format_subfinder_results(tool_result: Dict[str, Any], findings: Dict[str, Any]) -> str:
        """Format subfinder results"""
        lines = ["\n### Subdomain Enumeration (Subfinder)"]
        
        status = tool_result.get('status', 'unknown')
        lines.append(f"- **Status**: {status}")
        
        subdomains = findings.get('list', [])
        if subdomains:
            lines.append(f"- **Total Found**: {len(subdomains)}")
            lines.append(f"\n**Key Subdomains** (top 10):")
            for i, subdomain in enumerate(subdomains[:10], 1):
                risk_indicator = ""
                subdomain_name = subdomain if isinstance(subdomain, str) else subdomain.get('domain', '')
                
                # Flag high-risk patterns
                if any(keyword in subdomain_name.lower() for keyword in ['admin', 'dev', 'test', 'staging']):
                    risk_indicator = " ⚠️ HIGH RISK"
                
                lines.append(f"{i}. `{subdomain_name}`{risk_indicator}")
            
            if len(subdomains) > 10:
                lines.append(f"\n*({len(subdomains) - 10} more subdomains discovered - see appendix)*")
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_nmap_results(tool_result: Dict[str, Any], findings: Dict[str, Any]) -> str:
        """Format nmap results"""
        lines = ["\n### Port Scanning (Nmap)"]
        
        status = tool_result.get('status', 'unknown')
        lines.append(f"- **Status**: {status}")
        
        open_ports = findings.get('open_ports', [])
        if open_ports:
            lines.append(f"- **Open Ports**: {len(open_ports)}")
            lines.append(f"\n**Port Details**:")
            
            for port_info in open_ports[:20]:  # Top 20 ports
                port = port_info.get('port', 'N/A')
                service = port_info.get('service', 'unknown')
                version = port_info.get('version', '')
                
                risk = ""
                if port in [3306, 5432, 27017, 6379, 1433]:
                    risk = " 🚨 **CRITICAL** - Database exposed"
                elif port in [22, 23, 21]:
                    risk = " ⚠️ Remote access"
                
                version_str = f" ({version})" if version else ""
                lines.append(f"- **Port {port}** - {service}{version_str}{risk}")
            
            if len(open_ports) > 20:
                lines.append(f"\n*({len(open_ports) - 20} more ports - see appendix)*")
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_httpx_results(tool_result: Dict[str, Any], findings: Dict[str, Any]) -> str:
        """Format httpx results"""
        lines = ["\n### HTTP Service Validation (httpx)"]
        
        alive_hosts = findings.get('alive', [])
        if alive_hosts:
            lines.append(f"- **Reachable Hosts**: {len(alive_hosts)}")
            lines.append(f"\n**Active Services**:")
            
            for host_info in alive_hosts[:15]:
                host = host_info if isinstance(host_info, str) else host_info.get('url', 'N/A')
                lines.append(f"- {host}")
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_whatweb_results(tool_result: Dict[str, Any], findings: Dict[str, Any]) -> str:
        """Format whatweb results"""
        lines = ["\n### Technology Detection (WhatWeb)"]
        
        tech_list = findings.get('list', [])
        if tech_list:
            lines.append(f"- **Technologies Detected**: {len(tech_list)}")
            lines.append(f"\n**Technology Stack**:")
            
            for tech in tech_list[:15]:
                tech_name = tech if isinstance(tech, str) else tech.get('name', 'Unknown')
                version = tech.get('version', '') if isinstance(tech, dict) else ''
                version_str = f" {version}" if version else ""
                
                lines.append(f"- {tech_name}{version_str}")
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_risk_profile(findings: Dict[str, Any]) -> str:
        """Format risk profile summary"""
        lines = []
        
        # Analyze findings for risks
        critical_risks = []
        high_risks = []
        medium_risks = []
        
        # Check for database exposure
        open_ports = findings.get('ports', {}).get('open_ports', [])
        for port_info in open_ports:
            port = port_info.get('port')
            if port in [3306, 5432, 27017]:
                critical_risks.append(f"Database port {port} exposed publicly")
        
        # Check for admin panels
        subdomains = findings.get('subdomains', {}).get('list', [])
        for subdomain in subdomains:
            subdomain_name = subdomain if isinstance(subdomain, str) else subdomain.get('domain', '')
            if 'admin' in subdomain_name.lower():
                high_risks.append(f"Admin panel discoverable: {subdomain_name}")
            elif any(keyword in subdomain_name.lower() for keyword in ['dev', 'test', 'staging']):
                medium_risks.append(f"Development environment exposed: {subdomain_name}")
        
        # Format risks
        if critical_risks:
            lines.append("\n### 🚨 Critical Issues (Immediate Action Required)")
            for risk in critical_risks:
                lines.append(f"- {risk}")
        
        if high_risks:
            lines.append("\n### ⚠️ High Priority Issues")
            for risk in high_risks:
                lines.append(f"- {risk}")
        
        if medium_risks:
            lines.append("\n### ℹ️ Medium Priority Issues")
            for risk in medium_risks[:5]:  # Top 5
                lines.append(f"- {risk}")
        
        if not (critical_risks or high_risks or medium_risks):
            lines.append("\n**No major security issues identified in reconnaissance phase.**")
            lines.append("\nHowever, deep vulnerability analysis is recommended to identify:")
            lines.append("- CVEs in detected software versions")
            lines.append("- Configuration weaknesses")
            lines.append("- Application-level vulnerabilities")
        
        return "\n".join(lines)
    
    @staticmethod
    def _generate_recommendations(findings: Dict[str, Any]) -> str:
        """Generate next steps recommendations"""
        lines = []
        
        lines.append("\nBased on reconnaissance findings, the following deep analysis is recommended:")
        lines.append("\n**Priority Actions**:")
        
        # Check what tools to recommend
        open_ports = findings.get('ports', {}).get('open_ports', [])
        has_web = any(p.get('port') in [80, 443, 8080, 8443] for p in open_ports)
        has_db = any(p.get('port') in [3306, 5432, 27017] for p in open_ports)
        
        if has_web:
            lines.append("1. **Nuclei Vulnerability Scan** - Check for known CVEs and misconfigurations in web services")
        
        if has_db:
            lines.append("2. **Database Security Assessment** - Verify authentication requirements and default credentials")
        
        lines.append("3. **Exploit Research** - Research exploits for identified software versions")
        lines.append("4. **Risk Prioritization** - Assess exploitability and business impact")
        lines.append("5. **Remediation Planning** - Generate actionable remediation steps")
        
        lines.append("\n**Analysis Focus**:")
        lines.append("- Exploit availability for detected versions")
        lines.append("- Configuration weaknesses")
        lines.append("- Authentication strength")
        lines.append("- Data exposure risks")
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_raw_outputs(tool_results: Dict[str, Any]) -> str:
        """Format raw outputs (truncated excerpts)"""
        lines = []
        
        for tool_name, result in tool_results.items():
            lines.append(f"\n### {tool_name.upper()} Raw Output (Excerpt)")
            
            raw_output = result.get('raw_output', '')
            if raw_output:
                # Truncate to first 500 chars
                excerpt = raw_output[:500]
                if len(raw_output) > 500:
                    excerpt += "\n\n... (output truncated) ..."
                
                lines.append(f"```\n{excerpt}\n```")
            else:
                lines.append("*(No raw output available)*")
        
        return "\n".join(lines)
    
    @staticmethod
    def _make_json_safe(text: str) -> str:
        """
        Ensure text is JSON-safe (no issues when serialized)
        
        This is CRITICAL to prevent '\n description' style errors
        """
        # Already in string format, so no need to escape newlines
        # (Markdown newlines are intentional and part of formatting)
        
        # Just ensure no null bytes or other problematic characters
        text = text.replace('\x00', '')
        
        return text
    
    @staticmethod
    def extract_findings_from_results(tool_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured findings from raw tool results
        
        Args:
            tool_results: Raw outputs from tools
            
        Returns:
            Structured findings dict
        """
        findings = {
            'subdomains': {'list': []},
            'ports': {'open_ports': []},
            'http_services': {'alive': []},
            'technologies': {'list': []},
            'services': [],
            'risk_level': 'MEDIUM'
        }
        
        # Extract from subfinder
        if 'subfinder' in tool_results:
            subfinder_data = tool_results['subfinder']
            if 'summary' in subfinder_data:
                findings['subdomains'] = subfinder_data['summary']
        
        # Extract from nmap
        if 'nmap' in tool_results:
            nmap_data = tool_results['nmap']
            if 'summary' in nmap_data:
                findings['ports'] = nmap_data['summary']
                findings['services'] = nmap_data['summary'].get('services', [])
        
        # Extract from httpx
        if 'httpx' in tool_results:
            httpx_data = tool_results['httpx']
            if 'summary' in httpx_data:
                findings['http_services'] = httpx_data['summary']
        
        # Extract from whatweb
        if 'whatweb' in tool_results:
            whatweb_data = tool_results['whatweb']
            if 'summary' in whatweb_data:
                findings['technologies'] = whatweb_data['summary']
        
        # Calculate risk level
        open_ports = findings['ports'].get('open_ports', [])
        critical_ports = [p for p in open_ports if p.get('port') in [3306, 5432, 27017, 6379, 1433]]
        
        if critical_ports:
            findings['risk_level'] = 'CRITICAL'
        elif len(open_ports) > 20:
            findings['risk_level'] = 'HIGH'
        elif len(open_ports) > 5:
            findings['risk_level'] = 'MEDIUM'
        else:
            findings['risk_level'] = 'LOW'
        
        return findings

