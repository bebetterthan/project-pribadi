"""
STRIX Foundation Layer - Shared Context
Layer 1.4: Shared Context/Memory

Purpose:
    Central data store where all agents can read and write scan data.
    Thread-safe, supports concurrent access.

Data Categories:
    - Scan configuration (target, type, settings)
    - Discovery data (subdomains, URLs, ports)
    - Findings (vulnerabilities, issues)
    - Agent notes (observations, recommendations)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from threading import Lock
from dataclasses import dataclass, field
import json


@dataclass
class DataEntry:
    """Single entry in shared context"""
    category: str  # discoveries, findings, notes, config
    key: str
    value: Any
    agent_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class SharedContext:
    """
    Thread-safe shared memory for agent collaboration.
    
    All agents can:
        - Read data from any category
        - Write data to any category
        - Query data with filters
        - Update existing data
    
    Concurrent access is safe (protected by locks).
    """
    
    def __init__(self, scan_id: str, target: str, config: Dict[str, Any]):
        """
        Initialize shared context.
        
        Args:
            scan_id: Unique scan identifier
            target: Scan target
            config: Scan configuration
        """
        self.scan_id = scan_id
        self.target = target
        self.config = config
        
        # Data storage
        self._data: Dict[str, List[DataEntry]] = {
            "config": [],
            "discoveries": [],
            "findings": [],
            "notes": [],
            "metadata": []
        }
        
        # Thread safety
        self._lock = Lock()
        
        # Metrics
        self.created_at = datetime.utcnow()
        self.read_count = 0
        self.write_count = 0
        
        # Store initial config
        self.store_data(
            category="config",
            key="scan_id",
            value=scan_id,
            agent_id="system"
        )
        self.store_data(
            category="config",
            key="target",
            value=target,
            agent_id="system"
        )
        self.store_data(
            category="config",
            key="settings",
            value=config,
            agent_id="system"
        )
    
    def store_data(
        self,
        category: str,
        key: str,
        value: Any,
        agent_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Store data in shared context.
        
        Args:
            category: Data category (discoveries, findings, notes, config)
            key: Data key
            value: Data value
            agent_id: Agent that wrote this data
            metadata: Optional metadata
        """
        with self._lock:
            if category not in self._data:
                self._data[category] = []
            
            entry = DataEntry(
                category=category,
                key=key,
                value=value,
                agent_id=agent_id,
                metadata=metadata or {}
            )
            
            self._data[category].append(entry)
            self.write_count += 1
    
    def get_data(
        self,
        category: str,
        key: Optional[str] = None,
        agent_id: Optional[str] = None
    ) -> List[DataEntry]:
        """
        Retrieve data from shared context.
        
        Args:
            category: Data category to query
            key: Optional filter by key
            agent_id: Optional filter by agent
        
        Returns:
            List of matching DataEntry objects
        """
        with self._lock:
            self.read_count += 1
            
            if category not in self._data:
                return []
            
            entries = self._data[category]
            
            # Apply filters
            if key:
                entries = [e for e in entries if e.key == key]
            if agent_id:
                entries = [e for e in entries if e.agent_id == agent_id]
            
            return entries
    
    def get_latest(self, category: str, key: str) -> Optional[Any]:
        """
        Get latest value for a specific key.
        
        Args:
            category: Data category
            key: Data key
        
        Returns:
            Latest value or None if not found
        """
        entries = self.get_data(category, key)
        if entries:
            # Return most recent
            latest = max(entries, key=lambda e: e.timestamp)
            return latest.value
        return None
    
    def update_data(
        self,
        category: str,
        key: str,
        value: Any,
        agent_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update existing data or create if doesn't exist.
        
        Args:
            category: Data category
            key: Data key
            value: New value
            agent_id: Agent updating data
            metadata: Optional metadata
        
        Returns:
            True if updated, False if created new
        """
        with self._lock:
            entries = [e for e in self._data.get(category, []) if e.key == key]
            
            if entries:
                # Update exists - add new version
                self.store_data(category, key, value, agent_id, metadata)
                return True
            else:
                # Create new
                self.store_data(category, key, value, agent_id, metadata)
                return False
    
    def query(
        self,
        category: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[DataEntry]:
        """
        Advanced query with multiple filters.
        
        Args:
            category: Optional category filter
            filters: Optional dict of filters
        
        Returns:
            List of matching entries
        """
        with self._lock:
            self.read_count += 1
            
            # Start with all data or specific category
            if category:
                results = self._data.get(category, [])
            else:
                results = []
                for entries in self._data.values():
                    results.extend(entries)
            
            # Apply filters
            if filters:
                for filter_key, filter_value in filters.items():
                    if filter_key == "agent_id":
                        results = [e for e in results if e.agent_id == filter_value]
                    elif filter_key == "key":
                        results = [e for e in results if e.key == filter_value]
                    elif filter_key == "after":
                        results = [e for e in results if e.timestamp > filter_value]
                    elif filter_key == "before":
                        results = [e for e in results if e.timestamp < filter_value]
            
            return results
    
    def get_all_discoveries(self) -> Dict[str, List[Any]]:
        """
        Get all discovery data organized by key.
        
        Returns:
            Dict of discovery data
        """
        discoveries = {}
        entries = self.get_data("discoveries")
        
        for entry in entries:
            if entry.key not in discoveries:
                discoveries[entry.key] = []
            discoveries[entry.key].append(entry.value)
        
        return discoveries
    
    def get_all_findings(self) -> List[Dict[str, Any]]:
        """
        Get all vulnerability findings.
        
        Returns:
            List of finding dicts
        """
        entries = self.get_data("findings")
        return [
            {
                "key": e.key,
                "value": e.value,
                "agent": e.agent_id,
                "timestamp": e.timestamp.isoformat(),
                "metadata": e.metadata
            }
            for e in entries
        ]
    
    def get_agent_notes(self, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get agent notes/observations.
        
        Args:
            agent_id: Optional filter by specific agent
        
        Returns:
            List of note dicts
        """
        entries = self.get_data("notes", agent_id=agent_id)
        return [
            {
                "agent": e.agent_id,
                "note": e.value,
                "timestamp": e.timestamp.isoformat(),
                "metadata": e.metadata
            }
            for e in entries
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get context statistics.
        
        Returns:
            Dict with statistics
        """
        with self._lock:
            total_entries = sum(len(entries) for entries in self._data.values())
            
            return {
                "scan_id": self.scan_id,
                "target": self.target,
                "created_at": self.created_at.isoformat(),
                "total_entries": total_entries,
                "entries_by_category": {
                    cat: len(entries) for cat, entries in self._data.items()
                },
                "read_count": self.read_count,
                "write_count": self.write_count,
                "agents_active": len(set(e.agent_id for entries in self._data.values() for e in entries))
            }
    
    def export(self) -> Dict[str, Any]:
        """
        Export all context data (for persistence).
        
        Returns:
            Serializable dict of all data
        """
        with self._lock:
            return {
                "scan_id": self.scan_id,
                "target": self.target,
                "config": self.config,
                "created_at": self.created_at.isoformat(),
                "data": {
                    category: [
                        {
                            "key": e.key,
                            "value": e.value,
                            "agent_id": e.agent_id,
                            "timestamp": e.timestamp.isoformat(),
                            "metadata": e.metadata
                        }
                        for e in entries
                    ]
                    for category, entries in self._data.items()
                },
                "stats": self.get_stats()
            }
    
    def __repr__(self) -> str:
        stats = self.get_stats()
        return f"<SharedContext scan={self.scan_id} entries={stats['total_entries']} reads={self.read_count} writes={self.write_count}>"


# =============================================================================
# Global Instance Management
# =============================================================================

_shared_context_instance: Optional[SharedContext] = None


def get_shared_context(
    scan_id: str = "test_scan",
    target: str = "example.com",
    config: Optional[Dict[str, Any]] = None
) -> SharedContext:
    """
    Get or create global shared context instance
    
    Args:
        scan_id: Scan identifier (only used if creating new instance)
        target: Scan target (only used if creating new instance)
        config: Scan configuration (only used if creating new instance)
    
    Returns:
        SharedContext instance
    """
    global _shared_context_instance
    if _shared_context_instance is None:
        _shared_context_instance = SharedContext(
            scan_id=scan_id,
            target=target,
            config=config or {}
        )
    return _shared_context_instance


def reset_shared_context():
    """Reset global shared context (for testing)"""
    global _shared_context_instance
    _shared_context_instance = None
