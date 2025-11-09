"""
STRIX Foundation Layer - Specialized Agents
Recon Agent: Reconnaissance and Discovery

Purpose:
    Discovers attack surface (subdomains, URLs, ports, technologies)
"""

from typing import Dict, Any, Optional
from app.strix.agents.base import BaseAgent, AgentType, AgentTask, AgentResult
from app.strix.agents.base import AgentState  # Use AgentState from base.py


class ReconAgent(BaseAgent):
    """
    Reconnaissance Agent
    
    Responsibilities:
        - Subdomain enumeration
        - Technology detection
        - Port scanning
        - Service discovery
    """
    
    def __init__(self, task: AgentTask, target: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Recon Agent.
        
        Args:
            task: Reconnaissance task
            target: Scan target
            config: Agent configuration
        """
        super().__init__(
            agent_type=AgentType.RECON,
            task=task,
            target=target,
            config=config
        )
        
        # Recon-specific state
        self.discoveries = {
            "subdomains": [],
            "urls": [],
            "ports": [],
            "technologies": []
        }
    
    def initialize(self) -> None:
        """Setup recon environment"""
        self._log("Recon agent initialized")
        self._log(f"Target: {self.target}")
        self._log(f"Task: {self.task.description}")
        
        # Send initial status
        self.send_message(
            msg_type="status_update",
            payload={
                "message": "Recon agent initialized and ready",
                "target": self.target
            }
        )
    
    def execute(self) -> AgentResult:
        """
        Execute reconnaissance task.
        
        Returns:
            AgentResult with discoveries
        """
        self._log("Starting reconnaissance")
        
        # TODO: Actual tool execution will be added in Layer 2
        # For now, placeholder logic to demonstrate agent structure
        
        try:
            # Simulate discovery (will be real tool execution in Layer 2)
            self._log("Discovering subdomains...")
            self.discoveries["subdomains"] = [
                f"www.{self.target}",
                f"mail.{self.target}",
                f"api.{self.target}"
            ]
            
            # Store discoveries in shared context
            if self.shared_context:
                self._log("Storing discoveries in shared context")
                self.shared_context.store_data(
                    category="discoveries",
                    key="subdomains",
                    value=self.discoveries["subdomains"],
                    agent_id=self.agent_id
                )
            
            # Notify other agents
            self.send_message(
                msg_type="data_share",
                payload={
                    "data_type": "subdomains",
                    "count": len(self.discoveries["subdomains"]),
                    "data": self.discoveries["subdomains"]
                },
                to="broadcast"  # All agents can see this
            )
            
            self._log(f"Reconnaissance complete. Found {len(self.discoveries['subdomains'])} subdomains")
            
            return AgentResult(
                success=True,
                data=self.discoveries,
                metadata={
                    "subdomains_count": len(self.discoveries["subdomains"]),
                    "target": self.target
                }
            )
            
        except Exception as e:
            self._log(f"Reconnaissance failed: {str(e)}", level="ERROR")
            return AgentResult(
                success=False,
                error=str(e)
            )
    
    def cleanup(self) -> None:
        """Clean up recon resources"""
        self._log("Cleaning up recon agent")
        # Cleanup logic here
    
    def handle_message(self, message: Dict[str, Any]) -> None:
        """
        Handle messages from orchestrator or other agents.
        
        Args:
            message: Message to handle
        """
        msg_type = message.get("type")
        payload = message.get("payload")
        
        if msg_type == "query":
            # Another agent asking for data
            query = payload.get("query") if payload else None
            
            if query == "subdomains":
                self.send_message(
                    msg_type="query_response",
                    payload={
                        "query": query,
                        "data": self.discoveries["subdomains"]
                    },
                    to=message.get("from")
                )
        
        elif msg_type == "pause":
            # Orchestrator requesting pause
            self.transition_state(AgentState.WAITING, "Paused by orchestrator")
        
        elif msg_type == "resume":
            # Orchestrator requesting resume
            self.transition_state(AgentState.RUNNING, "Resumed by orchestrator")
        
        else:
            self._log(f"Unknown message type: {msg_type}", level="DEBUG")
