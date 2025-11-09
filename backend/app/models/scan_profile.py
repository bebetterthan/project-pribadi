"""
Scan Profile Models
Fase 3.5: Pre-configured scan profiles for optimal UX
"""

from dataclasses import dataclass
from typing import Dict, Any, List
from enum import Enum

class ProfileType(str, Enum):
    """Scan profile types"""
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"
    CUSTOM = "custom"

@dataclass
class ToolConfig:
    """Configuration for a specific tool in a profile"""
    timeout: int  # seconds
    flags: Dict[str, Any]  # tool-specific flags
    enabled: bool = True

@dataclass
class ScanProfile:
    """
    Pre-configured scan profile
    Defines settings for all tools in a consistent way
    """
    name: str
    profile_type: ProfileType
    description: str
    estimated_duration: int  # seconds
    
    # Tool configurations
    subfinder_config: ToolConfig
    httpx_config: ToolConfig
    nmap_config: ToolConfig
    nuclei_config: ToolConfig
    whatweb_config: ToolConfig
    ffuf_config: ToolConfig
    sslscan_config: ToolConfig
    
    def get_tool_config(self, tool_name: str) -> ToolConfig:
        """Get configuration for a specific tool"""
        config_map = {
            'subfinder': self.subfinder_config,
            'httpx': self.httpx_config,
            'nmap': self.nmap_config,
            'nuclei': self.nuclei_config,
            'whatweb': self.whatweb_config,
            'ffuf': self.ffuf_config,
            'sslscan': self.sslscan_config,
        }
        return config_map.get(tool_name)


# =============================================================================
# PRE-CONFIGURED PROFILES
# =============================================================================

QUICK_PROFILE = ScanProfile(
    name="Quick Scan",
    profile_type=ProfileType.QUICK,
    description="Fast reconnaissance for initial assessment (5-10 minutes)",
    estimated_duration=600,  # 10 minutes
    
    subfinder_config=ToolConfig(
        timeout=60,  # 1 minute
        flags={'timeout_seconds': 60, 'sources': 'crtsh,censys'}  # Limited sources
    ),
    
    httpx_config=ToolConfig(
        timeout=30,
        flags={'timeout': 3}  # Quick probe
    ),
    
    nmap_config=ToolConfig(
        timeout=180,  # 3 minutes
        flags={'scan_profile': 'quick'}  # Top 100 ports only
    ),
    
    nuclei_config=ToolConfig(
        timeout=300,  # 5 minutes
        flags={
            'severity_filter': 'critical',  # Critical only
            'template_category': 'cves',
        }
    ),
    
    whatweb_config=ToolConfig(
        timeout=30,
        flags={'aggression_level': 1},  # Stealthy
        enabled=False  # Skip for quick scan
    ),
    
    ffuf_config=ToolConfig(
        timeout=120,  # 2 minutes
        flags={'wordlist_size': 'quick', 'extensions': ''},
        enabled=False  # Skip for quick scan
    ),
    
    sslscan_config=ToolConfig(
        timeout=60,
        flags={},
        enabled=False  # Skip for quick scan
    ),
)

STANDARD_PROFILE = ScanProfile(
    name="Standard Scan",
    profile_type=ProfileType.STANDARD,
    description="Balanced scan for most use cases (15-30 minutes)",
    estimated_duration=1800,  # 30 minutes
    
    subfinder_config=ToolConfig(
        timeout=180,  # 3 minutes
        flags={'timeout_seconds': 180}  # All free sources
    ),
    
    httpx_config=ToolConfig(
        timeout=60,
        flags={'timeout': 5}
    ),
    
    nmap_config=ToolConfig(
        timeout=600,  # 10 minutes
        flags={'scan_profile': 'normal'}  # Top 1000 ports + service detection
    ),
    
    nuclei_config=ToolConfig(
        timeout=900,  # 15 minutes
        flags={
            'severity_filter': 'critical,high',  # Critical + High
            'template_category': 'all',
        }
    ),
    
    whatweb_config=ToolConfig(
        timeout=60,
        flags={'aggression_level': 3},  # Aggressive
        enabled=True
    ),
    
    ffuf_config=ToolConfig(
        timeout=300,  # 5 minutes
        flags={'wordlist_size': 'standard', 'extensions': ''},
        enabled=True
    ),
    
    sslscan_config=ToolConfig(
        timeout=120,
        flags={},
        enabled=True
    ),
)

DEEP_PROFILE = ScanProfile(
    name="Deep Scan",
    profile_type=ProfileType.DEEP,
    description="Comprehensive analysis, full coverage (1-2 hours)",
    estimated_duration=7200,  # 2 hours
    
    subfinder_config=ToolConfig(
        timeout=300,  # 5 minutes
        flags={'timeout_seconds': 300}  # All sources, max timeout
    ),
    
    httpx_config=ToolConfig(
        timeout=120,
        flags={'timeout': 10}  # Longer timeout for slow targets
    ),
    
    nmap_config=ToolConfig(
        timeout=3600,  # 1 hour
        flags={'scan_profile': 'aggressive'}  # All 65535 ports + OS detection + scripts
    ),
    
    nuclei_config=ToolConfig(
        timeout=3600,  # 1 hour
        flags={
            'severity_filter': 'all',  # All severities
            'template_category': 'all',
        }
    ),
    
    whatweb_config=ToolConfig(
        timeout=120,
        flags={'aggression_level': 4},  # Heavy
        enabled=True
    ),
    
    ffuf_config=ToolConfig(
        timeout=1800,  # 30 minutes
        flags={'wordlist_size': 'deep', 'extensions': 'php,html,txt,zip,bak,sql'},
        enabled=True
    ),
    
    sslscan_config=ToolConfig(
        timeout=180,
        flags={},
        enabled=True
    ),
)


# Profile Registry
PROFILES = {
    ProfileType.QUICK: QUICK_PROFILE,
    ProfileType.STANDARD: STANDARD_PROFILE,
    ProfileType.DEEP: DEEP_PROFILE,
}


def get_profile(profile_type: str) -> ScanProfile:
    """Get a scan profile by type"""
    try:
        profile_enum = ProfileType(profile_type.lower())
        return PROFILES[profile_enum]
    except (ValueError, KeyError):
        # Default to standard if unknown
        return STANDARD_PROFILE


def list_profiles() -> List[Dict[str, Any]]:
    """List all available profiles"""
    return [
        {
            'type': profile.profile_type.value,
            'name': profile.name,
            'description': profile.description,
            'estimated_duration': profile.estimated_duration,
        }
        for profile in PROFILES.values()
    ]

