"""
Result Aggregator
Collect and merge results from multiple agents
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict


@dataclass
class AgentResult:
    """Result from single agent"""
    agent_id: str
    agent_type: str
    task_id: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    execution_time_ms: float = 0.0


class ResultAggregator:
    """
    Aggregate and merge results from multiple agents
    
    Features:
    - Collect results by category
    - Deduplicate findings
    - Generate unified report
    - Calculate statistics
    """
    
    def __init__(self):
        """Initialize result aggregator"""
        self.results: List[AgentResult] = []
        self.results_by_type: Dict[str, List[AgentResult]] = defaultdict(list)
        self.results_by_agent: Dict[str, List[AgentResult]] = defaultdict(list)
    
    def add_result(self, result: AgentResult) -> None:
        """
        Add agent result
        
        Args:
            result: Agent result to add
        """
        self.results.append(result)
        self.results_by_type[result.agent_type].append(result)
        self.results_by_agent[result.agent_id].append(result)
    
    def get_results_by_type(self, agent_type: str) -> List[AgentResult]:
        """Get all results from specific agent type"""
        return self.results_by_type.get(agent_type, [])
    
    def get_results_by_agent(self, agent_id: str) -> List[AgentResult]:
        """Get all results from specific agent"""
        return self.results_by_agent.get(agent_id, [])
    
    def aggregate_subdomains(self) -> Dict[str, Any]:
        """
        Aggregate subdomain findings from all reconnaissance agents
        
        Returns:
            Merged subdomain data
        """
        all_subdomains = set()
        sources = defaultdict(int)
        
        # Collect from reconnaissance results
        recon_results = self.get_results_by_type("reconnaissance")
        
        for result in recon_results:
            data = result.data
            if "subdomains" in data:
                all_subdomains.update(data["subdomains"])
            if "sources" in data:
                for source, count in data["sources"].items():
                    sources[source] += count
        
        return {
            "subdomains": sorted(all_subdomains),
            "count": len(all_subdomains),
            "sources": dict(sources),
            "source_count": len(sources)
        }
    
    def aggregate_ports(self) -> Dict[str, Any]:
        """
        Aggregate port scan findings from enumeration agents
        
        Returns:
            Merged port data
        """
        hosts_data = {}
        all_services = defaultdict(int)
        
        # Collect from enumeration results
        enum_results = self.get_results_by_type("enumeration")
        
        for result in enum_results:
            data = result.data
            if "hosts" in data:
                for host in data["hosts"]:
                    addr = host.get("address", "unknown")
                    if addr not in hosts_data:
                        hosts_data[addr] = {"ports": [], "services": {}}
                    
                    hosts_data[addr]["ports"].extend(host.get("ports", []))
                    
                    # Count services
                    for port in host.get("ports", []):
                        service = port.get("service", "unknown")
                        all_services[service] += 1
        
        return {
            "hosts": len(hosts_data),
            "hosts_data": hosts_data,
            "total_open_ports": sum(
                len(data["ports"]) for data in hosts_data.values()
            ),
            "services": dict(all_services)
        }
    
    def aggregate_vulnerabilities(self) -> Dict[str, Any]:
        """
        Aggregate vulnerability findings
        
        Returns:
            Merged vulnerability data
        """
        vulnerabilities = []
        severity_counts = defaultdict(int)
        
        # Collect from vulnerability scan results
        vuln_results = self.get_results_by_type("vulnerability_scanner")
        
        for result in vuln_results:
            data = result.data
            if "vulnerabilities" in data:
                for vuln in data["vulnerabilities"]:
                    vulnerabilities.append(vuln)
                    severity = vuln.get("severity", "unknown")
                    severity_counts[severity] += 1
        
        return {
            "total_vulnerabilities": len(vulnerabilities),
            "by_severity": dict(severity_counts),
            "vulnerabilities": vulnerabilities
        }
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive unified report
        
        Returns:
            Complete scan report
        """
        # Calculate execution statistics
        total_execution_time = sum(r.execution_time_ms for r in self.results)
        agent_types = set(r.agent_type for r in self.results)
        
        report = {
            "summary": {
                "scan_completed_at": datetime.utcnow().isoformat(),
                "total_agents": len(self.results_by_agent),
                "agent_types": list(agent_types),
                "total_tasks": len(self.results),
                "total_execution_time_ms": total_execution_time
            },
            "findings": {
                "subdomains": self.aggregate_subdomains(),
                "ports": self.aggregate_ports(),
                "vulnerabilities": self.aggregate_vulnerabilities()
            },
            "agent_breakdown": {}
        }
        
        # Add per-agent statistics
        for agent_id, results in self.results_by_agent.items():
            report["agent_breakdown"][agent_id] = {
                "result_count": len(results),
                "execution_time_ms": sum(r.execution_time_ms for r in results),
                "agent_type": results[0].agent_type if results else "unknown"
            }
        
        return report
    
    def get_stats(self) -> Dict[str, Any]:
        """Get aggregator statistics"""
        return {
            "total_results": len(self.results),
            "results_by_type": {
                agent_type: len(results)
                for agent_type, results in self.results_by_type.items()
            },
            "results_by_agent": {
                agent_id: len(results)
                for agent_id, results in self.results_by_agent.items()
            }
        }
    
    def clear(self) -> None:
        """Clear all results"""
        self.results.clear()
        self.results_by_type.clear()
        self.results_by_agent.clear()
